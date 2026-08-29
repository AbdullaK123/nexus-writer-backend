export class AbortControllerSlot {
    private controller: AbortController | null = null

    replace(): AbortController {
        this.controller?.abort()
        this.controller = new AbortController()
        return this.controller
    }

    abort(): void {
        this.controller?.abort()
        this.controller = null
    }

    get current(): AbortController | null {
        return this.controller
    }
}
