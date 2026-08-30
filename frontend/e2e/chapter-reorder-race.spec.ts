import { expect, test, type Locator, type Page } from "@playwright/test";
import {
  API_BASE_URL,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

async function dragChapter(page: Page, sourceTitle: string, targetTitle: string) {
  const sourceTitleNode = page.getByRole("heading", { name: sourceTitle, exact: true, level: 4 });
  const targetTitleNode = page.getByRole("heading", { name: targetTitle, exact: true, level: 4 });
  const source = sourceTitleNode.locator("..");
  const target = targetTitleNode.locator("..");
  await expect(source).toBeVisible();
  await expect(target).toBeVisible();

  const sourceBox = await source.boundingBox();
  const targetBox = await target.boundingBox();
  expect(sourceBox, `sortable source ${sourceTitle} must have a real browser layout box`).not.toBeNull();
  expect(targetBox, `sortable target ${targetTitle} must have a real browser layout box`).not.toBeNull();

  await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetBox!.x + targetBox!.width / 2, targetBox!.y + targetBox!.height / 2, { steps: 12 });
  await page.mouse.up();
}

function applyMove<T>(items: T[], fromPos: number, toPos: number): T[] {
  const next = [...items];
  const [moved] = next.splice(fromPos, 1);
  if (moved === undefined) throw new Error(`invalid reorder source index ${fromPos}`);
  next.splice(toPos, 0, moved);
  return next;
}

test("conflicting chapter reorders must execute sequentially and preserve a valid total order", async ({ page, request }) => {
  const user = uniqueUser("reorder-race");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Reorder Race ${Date.now()}`);
  const titles = [0, 1, 2, 3].map((i) => `ORDER-${i}-${Date.now()}`);
  const ids: string[] = [];
  for (const title of titles) ids.push(await createChapter(browserRequest, storyId, title));

  let requestCount = 0;
  const payloads: Array<{ fromPos: number; toPos: number }> = [];
  let releaseFirst!: () => void;
  const firstMayFinish = new Promise<void>((resolve) => {
    releaseFirst = resolve;
  });

  await page.route(`**/api/stories/${storyId}/chapters/reorder`, async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    requestCount += 1;
    payloads.push(route.request().postDataJSON() as { fromPos: number; toPos: number });
    if (requestCount === 1) await firstMayFinish;
    await route.continue();
  });

  await page.goto(`/stories/${storyId}/${ids[0]}`);
  await expect(page.getByRole("heading", { name: titles[0], exact: true, level: 4 })).toBeVisible();

  await dragChapter(page, titles[0], titles[2]);
  await expect.poll(() => requestCount, {
    message: "the first drag must reach the real reorder endpoint before the second conflicting intent is issued",
  }).toBe(1);

  await dragChapter(page, titles[3], titles[1]);
  await page.waitForTimeout(300);
  expect(
    requestCount,
    "chapter reorder mutations must serialize while an older reorder is in flight; concurrent positional writes can apply against different orders and corrupt chapter numbering",
  ).toBe(1);

  releaseFirst();
  await expect.poll(() => requestCount, {
    message: "the second user reorder must execute after the first settles rather than being dropped",
    timeout: 10_000,
  }).toBe(2);

  await expect.poll(async () => {
    const response = await browserRequest.get(`${API_BASE_URL}/stories/${storyId}/chapters`);
    if (!response.ok()) return [] as string[];
    const body = (await response.json()) as { chapters: Array<{ chapterId: string }> };
    return body.chapters.map((chapter) => chapter.chapterId);
  }, {
    message: "both serialized reorder requests must settle before canonical ordering is checked",
    timeout: 10_000,
  }).toEqual(applyMove(applyMove(ids, payloads[0]!.fromPos, payloads[0]!.toPos), payloads[1]!.fromPos, payloads[1]!.toPos));

  const finalResponse = await browserRequest.get(`${API_BASE_URL}/stories/${storyId}/chapters`);
  expect(finalResponse.ok()).toBe(true);
  const finalBody = (await finalResponse.json()) as { chapters: Array<{ chapterId: string; chapterNumber: number }> };
  expect(new Set(finalBody.chapters.map((chapter) => chapter.chapterId)).size, "reordering must never duplicate or lose a chapter id").toBe(ids.length);
  expect(
    finalBody.chapters.map((chapter) => chapter.chapterNumber),
    "chapter numbers must remain a contiguous total order after conflicting reorders; gaps or duplicates poison navigation and every downstream chapter-relative query",
  ).toEqual([1, 2, 3, 4]);
});
