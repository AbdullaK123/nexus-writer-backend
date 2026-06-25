import { z } from "zod"
import { DateTimeSchema, StoryStatusSchema } from "./common"

// ─── Requests ────────────────────────────────────────────────

export const CreateChapterRequestSchema = z.object({
    title: z.string().min(1).max(255),
    content: z.string().default(""),
})
export type CreateChapterRequest = z.infer<typeof CreateChapterRequestSchema>

export const UpdateChapterRequestSchema = z.object({
    title: z.string().min(1).max(255).optional(),
    content: z.string().optional(),
    published: z.boolean().optional(),
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
    createdAt: DateTimeSchema,
    updatedAt: DateTimeSchema,
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