import { QueryClient } from "@tanstack/react-query"

export function createIntegrationQueryClient(): QueryClient {
    return new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
                staleTime: 0,
                gcTime: Infinity,
            },
            mutations: {
                retry: false,
            },
        },
    })
}

export type Deferred<T> = {
    promise: Promise<T>
    resolve: (value: T | PromiseLike<T>) => void
    reject: (reason?: unknown) => void
}

export function deferred<T>(): Deferred<T> {
    let resolve!: Deferred<T>["resolve"]
    let reject!: Deferred<T>["reject"]

    const promise = new Promise<T>((res, rej) => {
        resolve = res
        reject = rej
    })

    return { promise, resolve, reject }
}

export async function flushMicrotasks(): Promise<void> {
    await Promise.resolve()
    await Promise.resolve()
}
