import { expect, test, type Page } from "@playwright/test";
import {
  API_BASE_URL,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

function chapterRow(page: Page, title: string) {
  return page.getByRole("heading", { name: title, exact: true, level: 4 }).locator("..");
}

async function dragChapter(page: Page, sourceTitle: string, targetTitle: string) {
  const source = chapterRow(page, sourceTitle);
  const target = chapterRow(page, targetTitle);
  await expect(source).toBeVisible();
  await expect(target).toBeVisible();

  const sourceBox = await source.boundingBox();
  const targetBox = await target.boundingBox();
  expect(sourceBox, `sortable source ${sourceTitle} must have a real browser layout box`).not.toBeNull();
  expect(targetBox, `sortable target ${targetTitle} must have a real browser layout box`).not.toBeNull();

  const sourceX = sourceBox!.x + sourceBox!.width / 2;
  const sourceY = sourceBox!.y + sourceBox!.height / 2;
  const targetX = targetBox!.x + targetBox!.width / 2;
  const targetCenterY = targetBox!.y + targetBox!.height / 2;
  const targetY = sourceY < targetCenterY
    ? targetBox!.y + targetBox!.height * 0.75
    : targetBox!.y + targetBox!.height * 0.25;

  await page.mouse.move(sourceX, sourceY);
  await page.mouse.down();
  await page.mouse.move(targetX, targetY, { steps: 16 });
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

  const payloads: Array<{ fromPos: number; toPos: number }> = [];
  let heldRouteCount = 0;
  let releaseFirst!: () => void;
  const firstMayFinish = new Promise<void>((resolve) => {
    releaseFirst = resolve;
  });

  page.on("request", (req) => {
    if (req.method() !== "POST" || !req.url().endsWith(`/api/stories/${storyId}/chapters/reorder`)) return;
    payloads.push(req.postDataJSON() as { fromPos: number; toPos: number });
  });

  await page.route(`**/api/stories/${storyId}/chapters/reorder`, async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    heldRouteCount += 1;
    if (heldRouteCount === 1) await firstMayFinish;
    await route.continue();
  });

  await page.goto(`/stories/${storyId}/${ids[0]}`);
  await expect(page.getByRole("heading", { name: titles[0], exact: true, level: 4 })).toBeVisible();

  await dragChapter(page, titles[0], titles[2]);
  await expect.poll(() => payloads.length, {
    message: "the first drag must emit a real reorder request before serialization behavior is tested",
  }).toBe(1);

  await expect(
    chapterRow(page, titles[3]),
    "while a reorder is unresolved, the UI must explicitly disable further sorting instead of accepting an ambiguous positional command that can be silently lost",
  ).toHaveAttribute("aria-disabled", "true");

  await dragChapter(page, titles[3], titles[0]);
  await page.waitForTimeout(300);
  expect(
    payloads.length,
    "a reorder attempted while the UI is explicitly locked must not leak a concurrent positional write to the server",
  ).toBe(1);

  releaseFirst();

  await expect(
    chapterRow(page, titles[3]),
    "sorting must become available again after the in-flight reorder settles; a permanent lock would trade data corruption for a dead UI",
  ).toHaveAttribute("aria-disabled", "false");

  await dragChapter(page, titles[3], titles[0]);
  await expect.poll(() => payloads.length, {
    message: "once the first reorder settles, the next valid drag must emit its own request",
    timeout: 10_000,
  }).toBe(2);

  const expectedOrder = applyMove(
    applyMove(ids, payloads[0]!.fromPos, payloads[0]!.toPos),
    payloads[1]!.fromPos,
    payloads[1]!.toPos,
  );

  await expect.poll(async () => {
    const response = await browserRequest.get(`${API_BASE_URL}/stories/${storyId}/chapters`);
    if (!response.ok()) return [] as string[];
    const body = (await response.json()) as { chapters: Array<{ chapterId: string }> };
    return body.chapters.map((chapter) => chapter.chapterId);
  }, {
    message: "both accepted reorder operations must settle before canonical ordering is checked",
    timeout: 10_000,
  }).toEqual(expectedOrder);

  const finalResponse = await browserRequest.get(`${API_BASE_URL}/stories/${storyId}/chapters`);
  expect(finalResponse.ok()).toBe(true);
  const finalBody = (await finalResponse.json()) as { chapters: Array<{ chapterId: string; chapterNumber: number }> };
  expect(new Set(finalBody.chapters.map((chapter) => chapter.chapterId)).size, "reordering must never duplicate or lose a chapter id").toBe(ids.length);
  expect(
    finalBody.chapters.map((chapter) => chapter.chapterNumber),
    "chapter numbers must remain a contiguous total order after sequential reorders; gaps or duplicates poison navigation and every downstream chapter-relative query",
  ).toEqual([1, 2, 3, 4]);
});
