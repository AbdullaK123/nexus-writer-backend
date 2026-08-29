export class AbortControllerSlot {
    private controller: AbortController | null = null

    replace(): AbortController {
        this.controller?.abort()
        this.controller = new AbortController()
        return this.controller
    }

    clearIfCurrent(controller: AbortController): void {
        if (this.controller === controller) {
            this.controller = null
        }
    }

    abort(): void {
        this.controller?.abort()
        this.controller = null
    }

    get current(): AbortController | null {
        return this.controller
    }
}
