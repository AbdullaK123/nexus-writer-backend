export type ReorderRequest = {
    fromPos: number
    toPos: number
}

export function buildReorderRequest(
    fromPos: number,
    toPos: number,
    itemCount: number,
): ReorderRequest | null {
    if (!Number.isInteger(fromPos) || !Number.isInteger(toPos)) return null
    if (fromPos < 0 || toPos < 0) return null
    if (fromPos >= itemCount || toPos >= itemCount) return null
    if (fromPos === toPos) return null

    return { fromPos, toPos }
}
