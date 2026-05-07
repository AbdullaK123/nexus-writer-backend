import { z } from "zod"

/** ISO-8601 datetime string from the backend (always Z-suffixed) → JS `Date`. */
export const DateTimeSchema = z.coerce.date()

/** Mirrors `StoryStatus` in `src/data/schemas/enums.py`. Values, not keys. */
export const StoryStatusSchema = z.enum(["Complete", "On Hiatus", "Ongoing"])
export type StoryStatus = z.infer<typeof StoryStatusSchema>

/** Scene tension/pacing enums from `src/data/schemas/scene.py`. */
export const TensionSchema = z.enum(["low", "medium", "high"])
export type Tension = z.infer<typeof TensionSchema>

export const PacingSchema = z.enum(["slow", "steady", "fast"])
export type Pacing = z.infer<typeof PacingSchema>
export const ApiMessageSchema = z.object({ message: z.string() })
export type ApiMessage = z.infer<typeof ApiMessageSchema>




