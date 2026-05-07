import { z } from "zod"
import { DateTimeSchema, StoryStatusSchema } from "./common"
import { ChapterListItemSchema } from "./chapter"

// ─── Requests ────────────────────────────────────────────────

export const CreateStoryRequestSchema = z.object({
    title: z.string().min(1).max(255),
})
export type CreateStoryRequest = z.infer<typeof CreateStoryRequestSchema>

export const UpdateStoryRequestSchema = z.object({
    title: z.string().min(1).max(255).optional(),
    status: StoryStatusSchema.optional(),
})
export type UpdateStoryRequest = z.infer<typeof UpdateStoryRequestSchema>

// ─── Responses ───────────────────────────────────────────────

export const StoryCardResponseSchema = z.object({
    id: z.string(),
    latestChapterId: z.string().nullable(),
    title: z.string(),
    status: StoryStatusSchema,
    totalChapters: z.number().int(),
    wordCount: z.number().int(),
    createdAt: DateTimeSchema,
    updatedAt: DateTimeSchema,
})
export type StoryCardResponse = z.infer<typeof StoryCardResponseSchema>

export const StoryDetailResponseSchema = StoryCardResponseSchema.extend({
    chapters: z.array(ChapterListItemSchema),
})
export type StoryDetailResponse = z.infer<typeof StoryDetailResponseSchema>

export const StoryGridResponseSchema = z.object({
    stories: z.array(StoryCardResponseSchema),
})
export type StoryGridResponse = z.infer<typeof StoryGridResponseSchema>