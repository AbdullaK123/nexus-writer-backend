import { z } from "zod"
import { Err, Ok, type Result } from "../shared/types"


// ─── Schema ──────────────────────────────────────────────────

const EnvSchema = z
    .object({
        VITE_API_BASE_URL: z
            .url()
            .refine((u) => !u.endsWith("/"), "VITE_API_URL must not end with '/'"),
        VITE_API_TIMEOUT_MS: z
            .coerce.number()
            .int()
            .positive("VITE_API_TIMEOUT_MS must be a positive integer"),
    })
    .strict()


// ─── Public types ────────────────────────────────────────────

export interface AppConfig {
    readonly api: {
        readonly baseURL: string
        readonly defaultTimeoutMs: number
    }
    readonly mode: string
    readonly isDev: boolean
    readonly isProd: boolean
}

export class ConfigError extends Error {
    public readonly name = "ConfigError" as const
    public readonly issues: ReadonlyArray<{ path: string; message: string }>

    constructor(issues: ReadonlyArray<{ path: string; message: string }>) {
        const summary = issues
            .map((i) => `  • ${i.path || "(root)"}: ${i.message}`)
            .join("\n")
        super(`Invalid frontend environment configuration:\n${summary}`)
        this.issues = issues
    }
}


// ─── Loader (no module-level side effects) ───────────────────

export function loadConfig(): Result<AppConfig, ConfigError> {
    const parsed = EnvSchema.safeParse(import.meta.env)

    if (!parsed.success) {
        return Err(
            new ConfigError(
                parsed.error.issues.map((i) => ({
                    path: i.path.join("."),
                    message: i.message,
                })),
            ),
        )
    }

    return Ok({
        api: {
            baseURL: parsed.data.VITE_API_BASE_URL,
            defaultTimeoutMs: parsed.data.VITE_API_TIMEOUT_MS,
        },
        mode: import.meta.env.MODE,
        isDev: import.meta.env.DEV,
        isProd: import.meta.env.PROD,
    })
}
