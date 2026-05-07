import { z } from "zod"
import { DateTimeSchema, TensionSchema, PacingSchema } from "./common"

// ─── Requests ────────────────────────────────────────────────

export const SceneSearchRequestSchema = z.object({
    query: z.string().min(1).max(500),
    k: z.number().int().min(1).max(50).nullable().optional(),
    candidatePool: z.number().int().min(1).max(500).nullable().optional(),
    tension: TensionSchema.nullable().optional(),
    pacing: PacingSchema.nullable().optional(),
    tags: z.array(z.string()).nullable().optional(),
    mentionedEntities: z.array(z.string()).nullable().optional(),
    chapterIds: z.array(z.string()).nullable().optional(),
})
export type SceneSearchRequest = z.infer<typeof SceneSearchRequestSchema>

// ─── Responses ───────────────────────────────────────────────

export const SceneSearchResponseSchema = z.object({
    id: z.string(),
    chapterId: z.string(),
    storyId: z.string(),
    title: z.string(),
    description: z.string(),
    startQuote: z.string(),
    endQuote: z.string(),
    tension: TensionSchema,
    pacing: PacingSchema,
    mentionedEntities: z.array(z.string()),
    tags: z.array(z.string()),
    questionsRaised: z.array(z.string()),
    score: z.number(),
    createdAt: DateTimeSchema,
    updatedAt: DateTimeSchema,
})
export type SceneSearchResponse = z.infer<typeof SceneSearchResponseSchema>

export const SceneSearchListResponseSchema = z.object({
    results: z.array(SceneSearchResponseSchema),
})
export type SceneSearchListResponse = z.infer<typeof SceneSearchListResponseSchema>

// ─── Vocabulary listing (tags / entities) ────────────────────

export const VocabularyItemSchema = z.object({
    value: z.string(),
    count: z.number().int(),
})
export type VocabularyItem = z.infer<typeof VocabularyItemSchema>

export const VocabularyListResponseSchema = z.object({
    items: z.array(VocabularyItemSchema),
})
export type VocabularyListResponse = z.infer<typeof VocabularyListResponseSchema>