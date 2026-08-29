export function isCurrentChapter(
    routeChapterId: string,
    responseChapterId: string,
): boolean {
    return routeChapterId === responseChapterId
}
