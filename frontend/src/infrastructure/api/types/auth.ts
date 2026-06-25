import { z } from "zod"
import { ChapterListItemSchema } from "./chapter";
import { None, Some } from "oxide.ts";

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
    profileImg: z.string().optional().transform((value) => {
        return value !== undefined ? Some(value) : None
    }),
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