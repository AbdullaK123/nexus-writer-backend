import { z } from "zod"
import { DateTimeSchema, StoryStatusSchema } from "./common"

// ─── Requests ────────────────────────────────────────────────

export const CreateChapterRequestSchema = z.object({
    title: z.string().min(1).max(255)
})
export type CreateChapterRequest = z.infer<typeof CreateChapterRequestSchema>

export const UpdateChapterRequestSchema = z.object({
    title: z.string().min(1).max(255).optional(),
    content: z.string().optional(),
    published: z.boolean().optional(),
    expectedRevision: z.string().optional(),
})
export type UpdateChapterRequest = z.infer<typeof UpdateChapterRequestSchema>

export const ReorderChapterRequestSchema = z.object({
    fromPos: z.number().int(),
    toPos: z.number().int(),
})
export type ReorderChapterRequest = z.infer<typeof ReorderChapterRequestSchema>

// ─── Responses ───────────────────────────────────────────────

export const ChapterListItemSchema = z.object({
    storyId: z.string(),
    chapterId: z.string(),
    chapterNumber: z.int(),
    wordCount: z.int().default(0),
    storyTitle: z.string(),
    chapterTitle: z.string(),
    published: z.boolean(),
    updatedAt: DateTimeSchema
})
export type ChapterListItem = z.infer<typeof ChapterListItemSchema>

export const ChapterContentResponseSchema = z.object({
    id: z.string(),
    title: z.string(),
    published: z.boolean(),
    content: z.string(),
    storyId: z.string(),
    storyTitle: z.string(),
    chapterNumber: z.int(),
    wordCount: z.int(),
    createdAt: DateTimeSchema,
    updatedAt: DateTimeSchema,
    revision: z.string().nullable().optional(),
    previousChapterId: z.string().nullable(),
    nextChapterId: z.string().nullable(),
})
export type ChapterContentResponse = z.infer<typeof ChapterContentResponseSchema>

export const ChapterListResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    storyStatus: StoryStatusSchema,
    storyLastUpdated: DateTimeSchema,
    chapters: z.array(ChapterListItemSchema),
})
export type ChapterListResponse = z.infer<typeof ChapterListResponseSchema>


export const ChapterSummaryResponseSchema = z.object({
    summary: z.string()
})

export type ChapterSummaryResponse = z.infer<typeof ChapterSummaryResponseSchema>


export const CommentCategorySchema = z.enum([
    "clarity",
    "continuity",
    "character",
    "plot",
    "structure",
    "pacing",
    "dialogue",
    "worldbuilding",
    "prose",
    "not-available",
])

export type CommentCategory = z.infer<typeof CommentCategorySchema>

export const CommentPrioritySchema = z.enum([
    "note",
    "suggestion",
    "important",
    "not-available",
])

export type CommentPriority = z.infer<typeof CommentPrioritySchema>

export const CommentScopeSchema = z.enum([
    "local",
    "chapter",
    "character-history",
    "manuscript",
    "not-available",
])

export type CommentScope = z.infer<typeof CommentScopeSchema>


export const CommentEvidenceSchema = z.object({
    quoted_text: z.string(),
    relevance: z.string()
})

export type CommentEvidence = z.infer<typeof CommentEvidenceSchema>


export const ExtractedCommentSchema = z.object({
    quoted_text: z.string(),
    title: z.string(),
    body: z.string(),
    category: CommentCategorySchema,
    priority: CommentPrioritySchema,
    scope: CommentScopeSchema,
    issue_key: z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/),
    evidence: z.array(CommentEvidenceSchema)
})

export type ExtractedComment = z.infer<typeof ExtractedCommentSchema>


export const CommentExtractionSchema = z.object({
    comments: z.array(ExtractedCommentSchema)
})

export type CommentExtraction = z.infer<typeof CommentExtractionSchema>


export const CommentExtractionResponseSchema = z.object({
    storyId: z.string(),
    storyTitle: z.string(),
    chapterId: z.string(),
    chapterNumber: z.number(),
    generatedAt: z.coerce.date(),
    extraction: CommentExtractionSchema
})

export type CommentExtractionResponse = z.infer<typeof CommentExtractionResponseSchema>