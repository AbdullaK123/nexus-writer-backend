export class LatestOperation {
    private revision = 0

    start(): number {
        this.revision += 1
        return this.revision
    }

    isLatest(revision: number): boolean {
        return revision === this.revision
    }

    invalidate(): void {
        this.revision += 1
    }
}
