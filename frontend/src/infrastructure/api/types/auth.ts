import { z } from "zod"
import { ChapterListItemSchema } from "./chapter";

// ─── Requests ────────────────────────────────────────────────

export const RegistrationDataSchema = z.object({
    username: z.string().min(1).max(100),
    email: z.email(),
    password: z.string().min(8).max(128),
    profileImg: z.string().nullable().optional(),
})
export type RegistrationData = z.infer<typeof RegistrationDataSchema>

export const AuthCredentialsSchema = z.object({
    email: z.email(),
    password: z.string(),
})
export type AuthCredentials = z.infer<typeof AuthCredentialsSchema>

// ─── Responses ───────────────────────────────────────────────

export const UserResponseSchema = z.object({
    id: z.string(),
    username: z.string(),
    email: z.string(),
    profileImg: z.string().optional().nullable(),
})
export type UserResponse = z.infer<typeof UserResponseSchema>

export const DashboardResponseSchema = z.object({
    totalWords: z.int().default(0),
    totalStories: z.int().default(0),
    chaptersTotal: z.int().default(0),
    chaptersPublished: z.int().default(0),
    scenesTracked: z.int().default(0),
    streakDays: z.int().default(0),
    jumpBackIn: z.array(ChapterListItemSchema)
})
export type DashboardResponse = z.infer<typeof DashboardResponseSchema>


export const NotificationSchema = z.object({
    kind: z.literal(["scenes_extracted", "analysis_ready", "comments_ready"]),
    story_id: z.string(),
    chapter_id: z.string(),
    message: z.string()
})

export type Notification = z.infer<typeof NotificationSchema>

export const UserNavigationRowSchema = z.object({
    chapterId: z.string(),
    storyId: z.string(),
    chapterNumber: z.number(),
    label: z.string()
})

export type UserNavigationRow = z.infer<typeof UserNavigationRowSchema>

export const UserNavigationResponseSchema = z.object({
    links: z.array(UserNavigationRowSchema)
})

export type UserNavigationResponse = z.infer<typeof UserNavigationResponseSchema>

export const StoryNavigationRowSchema = z.object({
    storyId: z.string(),
    title: z.string()
})

export type StoryNavigationRow = z.infer<typeof StoryNavigationRowSchema>

export const StoryNavigationResponseSchema = z.object({
    links: z.array(StoryNavigationRowSchema)
})

export type StoryNavigationResponse = z.infer<typeof StoryNavigationResponseSchema>