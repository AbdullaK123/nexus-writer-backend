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
export const AppearanceSettingsSchema = z.object({
    theme: z.enum(["system", "light", "dark"]).default("system"),
    reduced_motion: z.boolean().default(false),
})
export type AppearanceSettings = z.infer<typeof AppearanceSettingsSchema>


export const EditorSettingsSchema = z.object({
    font_family: z.string().default("Literata"),
    font_size: z.number().int().default(18),
    line_height: z.number().default(1.7),
    content_width: z.number().int().default(760),
    spellcheck: z.boolean().default(true),
})
export type EditorSettings = z.infer<typeof EditorSettingsSchema>


export const NotificationSettingsSchema = z.object({
    analysis_ready: z.boolean().default(true),
    comments_ready: z.boolean().default(true),
    job_failures: z.boolean().default(true),
})
export type NotificationSettings = z.infer<typeof NotificationSettingsSchema>


export const AppearanceSettingsPayloadSchema = z.object({
    kind: z.literal("appearance"),
    appearance: AppearanceSettingsSchema,
})


export const EditorSettingsPayloadSchema = z.object({
    kind: z.literal("editor"),
    editor: EditorSettingsSchema,
})


export const NotificationSettingsPayloadSchema = z.object({
    kind: z.literal("notifications"),
    notifications: NotificationSettingsSchema,
})


export const SettingsPayloadSchema = z.discriminatedUnion("kind", [
    AppearanceSettingsPayloadSchema,
    EditorSettingsPayloadSchema,
    NotificationSettingsPayloadSchema,
])
export type SettingsPayload = z.infer<typeof SettingsPayloadSchema>


export const UserSettingsSchema = z.object({
    appearance: AppearanceSettingsSchema,
    editor: EditorSettingsSchema,
    notifications: NotificationSettingsSchema,
})
export type UserSettings = z.infer<typeof UserSettingsSchema> | Record<string, never>

export const UserResponseSchema = z.object({
    id: z.string(),
    username: z.string(),
    email: z.string(),
    profileImg: z.string().optional().nullable(),
    settings: UserSettingsSchema
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
    kind: z.literal(["scenes_extracted", "analysis_ready", "comments_ready", "job_failed"]),
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