import { describe, expect, test } from "vitest"

import {
    DashboardResponseSchema,
    NotificationSchema,
    UserResponseSchema,
} from "../../../src/infrastructure/api/types/auth"
import {
    ChapterContentResponseSchema,
    ChapterListResponseSchema,
} from "../../../src/infrastructure/api/types/chapter"
import {
    ChatMessageListResponseSchema,
    ThreadListResponseSchema,
} from "../../../src/infrastructure/api/types/chat"
import {
    SceneSearchListResponseSchema,
    VocabularyListResponseSchema,
} from "../../../src/infrastructure/api/types/scene"
import {
    StoryDetailResponseSchema,
    StoryGridResponseSchema,
} from "../../../src/infrastructure/api/types/story"

const now = "2026-08-29T10:00:00Z"

const chapterListItem = {
    storyId: "story-1",
    chapterId: "chapter-1",
    chapterNumber: 1,
    wordCount: 1200,
    storyTitle: "The Black Harbor",
    chapterTitle: "Arrival",
    published: false,
    updatedAt: now,
}

const storyCard = {
    storyId: "story-1",
    status: "Ongoing",
    chapterNumber: 1,
    title: "The Black Harbor",
    wordCount: 1200,
    updatedAt: now,
}

describe("API response schemas", () => {
    test("accepts backend-shaped story payloads and coerces datetimes", () => {
        const detail = StoryDetailResponseSchema.parse({
            ...storyCard,
            chapters: [chapterListItem],
        })
        const grid = StoryGridResponseSchema.parse({ stories: [storyCard] })

        expect(detail.updatedAt).toBeInstanceOf(Date)
        expect(detail.chapters[0]?.updatedAt).toBeInstanceOf(Date)
        expect(grid.stories).toHaveLength(1)
    })

    test("rejects snake_case story response fields", () => {
        expect(
            StoryDetailResponseSchema.safeParse({
                story_id: "story-1",
                status: "Ongoing",
                chapter_number: 1,
                title: "The Black Harbor",
                word_count: 1200,
                updated_at: now,
                chapters: [],
            }).success,
        ).toBe(false)
    })

    test("accepts chapter list and chapter content payloads", () => {
        const list = ChapterListResponseSchema.parse({
            storyId: "story-1",
            storyTitle: "The Black Harbor",
            storyStatus: "Ongoing",
            storyLastUpdated: now,
            chapters: [chapterListItem],
        })
        const chapter = ChapterContentResponseSchema.parse({
            id: "chapter-1",
            title: "Arrival",
            published: false,
            content: "<p>Hello</p>",
            storyId: "story-1",
            storyTitle: "The Black Harbor",
            chapterNumber: 1,
            wordCount: 1,
            createdAt: now,
            updatedAt: now,
            previousChapterId: null,
            nextChapterId: "chapter-2",
        })

        expect(list.storyLastUpdated).toBeInstanceOf(Date)
        expect(chapter.nextChapterId).toBe("chapter-2")
    })

    test("rejects chapter navigation fields with the wrong nullability", () => {
        expect(
            ChapterContentResponseSchema.safeParse({
                id: "chapter-1",
                title: "Arrival",
                published: false,
                content: "",
                storyId: "story-1",
                storyTitle: "The Black Harbor",
                chapterNumber: 1,
                wordCount: 0,
                createdAt: now,
                updatedAt: now,
                previousChapterId: 1,
                nextChapterId: null,
            }).success,
        ).toBe(false)
    })

    test("accepts thread lists and rejects malformed thread timestamps", () => {
        expect(
            ThreadListResponseSchema.safeParse({
                threads: [
                    {
                        threadId: "thread-1",
                        threadTitle: "Ideas",
                        updatedAt: now,
                    },
                ],
            }).success,
        ).toBe(true)

        expect(
            ThreadListResponseSchema.safeParse({
                threads: [
                    {
                        threadId: "thread-1",
                        threadTitle: "Ideas",
                        updatedAt: "not-a-date",
                    },
                ],
            }).success,
        ).toBe(false)
    })

    test("requires the chat message response envelope", () => {
        expect(
            ChatMessageListResponseSchema.safeParse({
                threadId: "thread-1",
                threadTitle: "Ideas",
                messages: [],
            }).success,
        ).toBe(true)

        expect(
            ChatMessageListResponseSchema.safeParse({ messages: [] }).success,
        ).toBe(false)
    })

    test("accepts scene search and vocabulary response envelopes", () => {
        const scene = {
            id: "scene-1",
            chapterId: "chapter-1",
            chapterNumber: 1,
            chapterTitle: "Arrival",
            storyId: "story-1",
            title: "Dockside",
            description: "Mara arrives.",
            startQuote: "Mara stepped ashore.",
            endQuote: "The bells rang.",
            tension: "medium",
            pacing: "steady",
            mentionedEntities: ["Mara"],
            tags: ["harbor"],
            questionsRaised: [],
            score: 0.91,
            createdAt: now,
            updatedAt: now,
        }

        expect(SceneSearchListResponseSchema.safeParse({ results: [scene] }).success).toBe(true)
        expect(
            VocabularyListResponseSchema.safeParse({
                items: [{ value: "Mara", count: 3 }],
            }).success,
        ).toBe(true)
    })

    test("rejects invalid scene enum values", () => {
        expect(
            SceneSearchListResponseSchema.safeParse({
                results: [
                    {
                        id: "scene-1",
                        chapterId: "chapter-1",
                        chapterNumber: 1,
                        chapterTitle: "Arrival",
                        storyId: "story-1",
                        title: "Dockside",
                        description: "Mara arrives.",
                        startQuote: "a",
                        endQuote: "b",
                        tension: "extreme",
                        pacing: "steady",
                        mentionedEntities: [],
                        tags: [],
                        questionsRaised: [],
                        score: 0.5,
                        createdAt: now,
                        updatedAt: now,
                    },
                ],
            }).success,
        ).toBe(false)
    })

    test("accepts a complete user response and rejects missing settings", () => {
        const user = {
            id: "user-1",
            username: "abdulla",
            email: "abdulla@example.com",
            profileImg: null,
            settings: {
                appearance: { theme: "system", reduced_motion: false },
                editor: {
                    font_family: "Literata",
                    font_size: 18,
                    line_height: 1.7,
                    content_width: 760,
                    spellcheck: true,
                },
                notifications: {
                    analysis_ready: true,
                    comments_ready: true,
                    job_failures: true,
                },
            },
        }

        expect(UserResponseSchema.safeParse(user).success).toBe(true)
        expect(UserResponseSchema.safeParse({ ...user, settings: undefined }).success).toBe(false)
    })

    test("accepts dashboard counters and jump-back-in chapters", () => {
        const dashboard = DashboardResponseSchema.parse({
            totalWords: 1200,
            totalStories: 1,
            chaptersTotal: 1,
            chaptersPublished: 0,
            scenesTracked: 3,
            streakDays: 2,
            jumpBackIn: [chapterListItem],
        })

        expect(dashboard.jumpBackIn).toHaveLength(1)
    })

    test.each([
        "scenes_extracted",
        "analysis_ready",
        "comments_ready",
        "job_failed",
    ] as const)("accepts notification kind %s", (kind) => {
        expect(
            NotificationSchema.safeParse({
                kind,
                story_id: "story-1",
                chapter_id: "chapter-1",
                message: "done",
            }).success,
        ).toBe(true)
    })

    test("rejects unknown notification kinds", () => {
        expect(
            NotificationSchema.safeParse({
                kind: "mystery_event",
                story_id: "story-1",
                chapter_id: "chapter-1",
                message: "done",
            }).success,
        ).toBe(false)
    })
})
