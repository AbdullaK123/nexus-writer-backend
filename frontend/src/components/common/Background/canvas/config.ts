import { z } from "zod"


const cssColor = z.string().regex(
    /^(#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})|(rgb|hsl)a?\([^)]+\))$/i,
    "must be a valid CSS color string",
)
const opacity = z.number().min(0).max(1)
const positive = z.number().positive()
const positiveInt = z.number().int().positive()


export const NodeAnimConfigSchema = z.object({
    color: cssColor.default("#7aa2ff"),
    radiusPx: positive.default(1.5),
    baseOpacity: opacity.default(0.6),
    pulseAmplitude: opacity.default(0.15),
    pulsePeriodMs: positive.default(4000)
}).strict()

export const EdgeAnimConfigSchema = z.object({
    color: cssColor.default("#8ef6fd"),
    widthPx: positive.default(0.75),
    baseOpacity: opacity.default(0.18)
}).strict()

export const PacketAnimConfigSchema = z.object({
    color: cssColor.default("#8bd7f5"),
    radius: positive.default(3.5),
    speedPxPerSec: positive.default(40000),
    trailLength: z.number().int().min(0).default(8),
    fadeInMs: z.number().min(0).default(250),
    fadeOutMs: z.number().min(0).default(250)
}).strict()

export const PathAnimConfigSchema = z.object({
    // Highlight along the active path while the packet traverses it.
    color:        cssColor.default("#7aa2ff"),
    widthPx:      positive.default(0.75),
    baseOpacity:  opacity.default(0.35),
}).strict()


export const SamplerConfigSchema = z.object({
    minDistancePx: positive.default(45),
    maxNodes: positiveInt.default(2000),
    seed: z.number().int().nonnegative().default(0xdecafbad)
}).strict()

export const PathSelectionConfigSchema = z.object({
    minEdges: positiveInt.default(6),
    maxEdges: positiveInt.default(20),
    selectionRetries: positiveInt.default(50)
}).strict().refine(
    (v) => v.maxEdges >= v.minEdges,
    { message: "maxEdges must be >= minEdges", path: ["maxEdges"] }
)

export const BackgroundConfigSchema = z.object({
    sampler: SamplerConfigSchema,
    pathSelection: PathSelectionConfigSchema,
    node: NodeAnimConfigSchema,
    edge: EdgeAnimConfigSchema,
    path: PathAnimConfigSchema,
    packet: PacketAnimConfigSchema,
    respectReducedMotion: z.boolean().default(true),
}).strict()


export type NodeAnimConfig      = z.infer<typeof NodeAnimConfigSchema>
export type EdgeAnimConfig      = z.infer<typeof EdgeAnimConfigSchema>
export type PacketAnimConfig    = z.infer<typeof PacketAnimConfigSchema>
export type PathAnimConfig      = z.infer<typeof PathAnimConfigSchema>
export type SamplerConfig       = z.infer<typeof SamplerConfigSchema>
export type PathSelectionConfig = z.infer<typeof PathSelectionConfigSchema>
export type BackgroundConfig    = z.infer<typeof BackgroundConfigSchema>

// Defaults: parse `{}` so defaults flow from the schema, not a parallel object.
export const DEFAULT_BACKGROUND_CONFIG: BackgroundConfig =
    BackgroundConfigSchema.parse({
        sampler: {},
        pathSelection: {},
        node: {},
        edge: {},
        path: {},
        packet: {},
        respectReducedMotion: true
    })

// Convenience for the React boundary: accept any partial override, validate.
export const parseBackgroundConfig = (
    input: unknown = {},
): BackgroundConfig => BackgroundConfigSchema.parse(input)