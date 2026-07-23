import { z } from "zod"


// ---------------------- CHARACTER types ----------------------------------------------------

export const AnalyticsSuggestionExtractionSchema = z.object({
    headline: z.string(),
    analysis: z.string(),
    status: z.enum(['healthy', 'worth-watching', 'needs-your-attention', 'not-available'])
})

export const AnalyticsSuggestionResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    generatedAt: z.date(),
    suggestion: AnalyticsSuggestionExtractionSchema
})

export type AnalyticsSuggestionResponse = z.infer<typeof AnalyticsSuggestionResponseSchema>

export const CastStatisticsRowSchema = z.object({
    character: z.string(),
    scene_count: z.number(),
    word_count: z.number()
})

export type CastStatisticsRow = z.infer<typeof CastStatisticsRowSchema>

export const CastStatisticsResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    statistics: z.array(CastStatisticsRowSchema)
})

export type CastStatisticsResponse = z.infer<typeof CastStatisticsResponseSchema>


export const CoOccurenceStatisticsRowSchema = z.object({
    character_a: z.string(),
    character_b: z.string(),
    scene_count: z.number(),
    word_count: z.number()
})

export const CoOccurenceStatisticsResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    statistics: z.array(CoOccurenceStatisticsRowSchema)
})

export type CoOccurenceStatisticsResponse = z.infer<typeof CoOccurenceStatisticsResponseSchema>

export const CharacterStatisticsRowSchema = z.object({
    chapter_id: z.string(),
    chapter_number: z.number(),
    pov: z.string(),
    scene_count: z.number(),
    word_count: z.number()
})

export const CharacterStatisticsResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    statistics: z.array(CharacterStatisticsRowSchema)
})

export type CharacterStatisticsResponse = z.infer<typeof CharacterStatisticsResponseSchema>

export const CharacterDashboardResponseSchema = z.object({
    suggestion: AnalyticsSuggestionResponseSchema,
    castStatistics: CastStatisticsResponseSchema,
    coOccurenceStatistics: CoOccurenceStatisticsResponseSchema,
    characterStatistics: CharacterStatisticsResponseSchema
})

export type CharacterDashboardResponse = z.infer<typeof CharacterDashboardResponseSchema>

//--------------------------------- Plot types -------------------------------------------------

export const PlotThreadSchema = z.object({
    name: z.string(),
    chapter_started: z.number(),
    chapter_ended: z.number().optional().nullable(),
    chapter_last_touched: z.number(),
    status: z.enum(['open', 'resolved', 'unknown'])
})

export const PlotThreadExtractionSchema = z.object({
    threads: z.array(PlotThreadSchema)
})

export const PlotThreadsResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    pathArray: z.array(z.string()),
    generatedAt:  z.date(),
    extraction: PlotThreadExtractionSchema
})

export type PlotThreadsResponse = z.infer<typeof PlotThreadsResponseSchema>

export const ActSchema = z.object({
    number: z.literal([1, 2, 3, 4]),
    chapter_started: z.number(),
    chapter_ended: z.number(),
    current_chapter: z.number().optional().nullable()
})

export const ActSegmentationExtractionSchema = z.object({
    acts: z.array(ActSchema)
})

export const ActSegmentationResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    pathArray: z.array(z.string()),
    generatedAt: z.date(),
    extraction: ActSegmentationExtractionSchema
})

export type ActSegmentationResponse = z.infer<typeof ActSegmentationResponseSchema>

export const PlotDashboardResponseSchema = z.object({
    suggestion: AnalyticsSuggestionResponseSchema,
    plotThreads: PlotThreadsResponseSchema,
    actSegmentation: ActSegmentationResponseSchema
})

export type PlotDashboardResponse = z.infer<typeof PlotDashboardResponseSchema>


// --------------------------------------- Structure types -------------------------------------
export const TensionCurveRowSchema = z.object({
    chapter_id: z.string(),
    chapter_number: z.number(),
    avg_tension: z.number()
})

export const PacingCurveRowSchema = z.object({
    chapter_id: z.string(),
    chapter_number: z.number(),
    avg_pacing: z.number()
})

export const TensionAndPacingCurveResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    tensionCurve: z.array(TensionCurveRowSchema),
    pacingCurve: z.array(PacingCurveRowSchema)
})

export type TensionAndPacingCurveResponse = z.infer<typeof TensionAndPacingCurveResponseSchema>


export const SceneLengthDistributionRowSchema = z.object({
    bin: z.string(),
    count: z.number()
})

export const SceneLengthDistributionResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    distribution: z.array(SceneLengthDistributionRowSchema)
})

export type SceneLengthDistributionResponse = z.infer<typeof SceneLengthDistributionResponseSchema>

export const StructureDashboardResponseSchema = z.object({
    suggestion: AnalyticsSuggestionResponseSchema,
    tensionAndPacingCurves: TensionAndPacingCurveResponseSchema,
    sceneLengthDistribution: SceneLengthDistributionResponseSchema,
    recentRythm: TensionAndPacingCurveResponseSchema
})

export type StructureDashboardResponse = z.infer<typeof StructureDashboardResponseSchema>

// ----------------------------------- World types ------------------------------------------------

export const ContradictionSchema = z.object({
    headline: z.string(),
    report: z.string(),
    relevant_chapters: z.array(z.number())
})

export const ContradictionExtractionSchema = z.object({
    contradictions: z.array(ContradictionSchema)
})

export const ContradictionResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    pathArray: z.array(z.string()),
    generatedAt: z.date(),
    extraction: ContradictionExtractionSchema
})

export type ContradictionResponse = z.infer<typeof ContradictionResponseSchema>

export const EntitySchema = z.object({
    type: z.literal(['place', 'faction', 'concept', 'system', 'character', 'other']),
    name: z.string(),
    chapterFirstAppeared: z.number(),
    chapterLastTouched: z.number()
})

export const EntityLedgerExtractionSchema = z.object({
    entities: z.array(EntitySchema)
})

export const EntityLedgerResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    pathArray: z.array(z.string()),
    generatedAt: z.date(),
    extraction: EntityLedgerExtractionSchema
})

export type EntityLedgerResponse = z.infer<typeof EntityLedgerResponseSchema>

export const WorldDashboardResponseSchema = z.object({
    suggestion: AnalyticsSuggestionResponseSchema,
    contradictions: ContradictionResponseSchema,
    entities: EntityLedgerResponseSchema
})

export type WorldDashboardResponse = z.infer<typeof WorldDashboardResponseSchema>