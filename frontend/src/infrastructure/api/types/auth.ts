import { z } from "zod"

// ─── Requests ────────────────────────────────────────────────

export const RegistrationDataSchema = z.object({
    username: z.string().min(1).max(100),
    email: z.string().email(),
    password: z.string().min(8).max(128),
    profileImg: z.string().nullable().optional(),
})
export type RegistrationData = z.infer<typeof RegistrationDataSchema>

export const AuthCredentialsSchema = z.object({
    email: z.string().email(),
    password: z.string(),
})
export type AuthCredentials = z.infer<typeof AuthCredentialsSchema>

// ─── Responses ───────────────────────────────────────────────

export const UserResponseSchema = z.object({
    id: z.string(),
    username: z.string(),
    email: z.string(),
    profileImg: z.string().nullable(),
})
export type UserResponse = z.infer<typeof UserResponseSchema>