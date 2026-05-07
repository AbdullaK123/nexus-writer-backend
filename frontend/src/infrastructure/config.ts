import {z} from "zod"


const EnvSchema = z.object({
    VITE_API_BASE_URL: z 
        .url()
        .refine((u) => !u.endsWith("/"), "VITE_API_URL must not end with '/'"),
    VITE_API_TIMEOUT_MS: z  
        .coerce
        .number()
        .int()
        .positive("VITE_API_TIMEOUT_MS must be a positive integer")
}).strict()


const parsed = EnvSchema.safeParse(import.meta.env)

if (!parsed.success) {
    const issues = parsed.error.issues
        .map((i) => `  • ${i.path.join(".") || "(root)"}: ${i.message}`)
        .join("\n")
    throw new Error(`Invalid frontend environment configuration:\n${issues}`)
}

export const config = Object.freeze({
    api: Object.freeze({
        baseURL: parsed.data.VITE_API_BASE_URL,
        defaultTimeoutMs: parsed.data.VITE_API_TIMEOUT_MS
    }),
    mode: import.meta.env.MODE,
    isDev: import.meta.env.DEV,
    isProd: import.meta.env.PROD
})

export type AppConfig = typeof config