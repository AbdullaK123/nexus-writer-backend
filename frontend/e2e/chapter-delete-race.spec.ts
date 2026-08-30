import { expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
  updateChapter,
} from "./helpers";

test("a delayed autosave cannot resurrect a chapter deleted while the write is in flight", async ({ page, request }) => {
  const user = uniqueUser("delete-race");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Delete Race ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Delete Me ${Date.now()}`);
  const baseline = `DELETE-BASELINE-${Date.now()}`;
  const stale = `STALE-WRITE-MUST-DIE-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  let intercepted = 0;
  let releaseWrite!: () => void;
  const mayContinue = new Promise<void>((resolve) => {
    releaseWrite = resolve;
  });

  await page.route(`**/api/chapters/${chapterId}`, async (route) => {
    if (route.request().method() !== "PUT") {
      await route.continue();
      return;
    }
    intercepted += 1;
    await mayContinue;
    await route.continue();
  });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor).toContainText(baseline);
  await editor.fill(stale);
  await expect.poll(() => intercepted, {
    message: "the stale autosave must be held at the network boundary before deletion occurs",
  }).toBe(1);

  const deletion = await browserRequest.delete(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(deletion.ok(), "the chapter must be successfully deleted while the older autosave is still suspended").toBe(true);

  releaseWrite();
  await page.waitForTimeout(1_000);

  const chapterResponse = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(
    chapterResponse.status(),
    "delayed network traffic must never resurrect user-deleted content; once deletion commits, a stale autosave must fail against the missing resource rather than recreating it",
  ).toBe(404);

  const listResponse = await browserRequest.get(`${API_BASE_URL}/stories/${storyId}/chapters`);
  expect(listResponse.ok()).toBe(true);
  const list = (await listResponse.json()) as { chapters: Array<{ chapterId: string }> };
  expect(
    list.chapters.some((chapter) => chapter.chapterId === chapterId),
    "the deleted chapter must remain absent from the story hierarchy after the suspended autosave is released",
  ).toBe(false);
});
