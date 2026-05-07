import { z } from "zod"
import { DateTimeSchema } from "./common"

/** Stored pydantic-ai ModelMessage dict — opaque to the frontend.
 * Render based on `kind` and `message.parts`. Keep as `unknown` until
 * a renderer is built that needs the structure. */
export const ChatMessagePayloadSchema = z.record(z.string(), z.unknown())
export type ChatMessagePayload = z.infer<typeof ChatMessagePayloadSchema>

export const ChatMessageKindSchema = z.enum(["request", "response"])
export type ChatMessageKind = z.infer<typeof ChatMessageKindSchema>

// ─── Request bodies ──────────────────────────────────────────
// Path supplies story_id / thread_id, so bodies are slim.

export const CreateThreadBodySchema = z.object({
    firstMessage: z.string().min(1),
})
export type CreateThreadBody = z.infer<typeof CreateThreadBodySchema>

export const TurnBodySchema = z.object({
    userMessage: z.string().min(1),
})
export type TurnBody = z.infer<typeof TurnBodySchema>

export const RenameThreadBodySchema = z.object({
    title: z.string().min(1),
})
export type RenameThreadBody = z.infer<typeof RenameThreadBodySchema>

// ─── Responses ───────────────────────────────────────────────

export const ThreadResponseSchema = z.object({
    threadId: z.string(),
    threadTitle: z.string(),
    updatedAt: DateTimeSchema,
})
export type ThreadResponse = z.infer<typeof ThreadResponseSchema>

export const ThreadListResponseSchema = z.object({
    threads: z.array(ThreadResponseSchema).nullable().default([]),
})
export type ThreadListResponse = z.infer<typeof ThreadListResponseSchema>

export const ChatMessageResponseSchema = z.object({
    sequence: z.number().int().nonnegative(),
    kind: ChatMessageKindSchema,
    message: ChatMessagePayloadSchema,
    createdAt: DateTimeSchema,
})
export type ChatMessageResponse = z.infer<typeof ChatMessageResponseSchema>

export const ChatMessageListResponseSchema = z.object({
    messages: z.array(ChatMessageResponseSchema).nullable().default([]),
})
export type ChatMessageListResponse = z.infer<typeof ChatMessageListResponseSchema>