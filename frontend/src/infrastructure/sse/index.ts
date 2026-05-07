import { createParser, type EventSourceMessage } from "eventsource-parser"


export interface SseHandlers {
    onEvent: (event: EventSourceMessage) => void;
    onClose?: () => void;
}

export interface SseRequest {
    url: string
    method?: "GET" | "POST"
    body?: unknown
    headers?: HeadersInit
    signal?: AbortSignal
}

export async function streamSse(
    request: SseRequest,
    handlers: SseHandlers
): Promise<void> {
    // send the request 
    const response = await fetch(
        request.url,
        {
            method: request.method ?? "POST",
            headers: {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                ...request.headers
            },
            body: request.body !== "undefined" ? JSON.stringify(request.body) : undefined,
            credentials: "same-origin",
            signal: request.signal
        }
    )

    // handle the case when the response fails
    if (!response.ok) {
        const text = await response.text()
        throw new Error(`SSE ${response.status}: ${text}`)
    }

    // handle the case when there's no body
    if (!response.body) {
        throw new Error("SSE response had no body")
    }

    // init the parser, the reader, and the decoder
    const parser = createParser({ onEvent: handlers.onEvent})
    const reader = response.body.getReader()
    const decoder = new TextDecoder() 

    // handle the stream
    try {
        while (true) {
            const {done, value} = await reader.read()
            if (done) break
            parser.feed(decoder.decode(value, {stream: true}))
        }
        handlers.onClose?.()

    } finally {
        reader.releaseLock()
    }
}