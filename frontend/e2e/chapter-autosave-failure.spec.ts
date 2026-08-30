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

test("a failed autosave cannot erase the user's unsaved editor buffer", async ({ page, request }) => {
  const user = uniqueUser("autosave-500");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Autosave Failure ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Failure Buffer ${Date.now()}`);
  const baseline = `SERVER-BASELINE-${Date.now()}`;
  const unsaved = `CLIENT-BUFFER-MUST-SURVIVE-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  let failedWrites = 0;
  await page.route(`**/api/chapters/${chapterId}`, async (route) => {
    if (route.request().method() !== "PUT") {
      await route.continue();
      return;
    }
    failedWrites += 1;
    await route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: "forced e2e failure" }) });
  });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor).toBeVisible();
  await expect(editor).toContainText(baseline);

  await editor.fill(unsaved);
  await expect.poll(() => failedWrites, {
    message: "the forced failure must intercept the real autosave PUT or this test proves nothing about rollback behavior",
    timeout: 5_000,
  }).toBe(1);

  await expect(
    editor,
    "a transient 500 may leave text unsaved, but it must never replace recoverable local prose with stale server content; network failure is not permission to destroy the user's buffer",
  ).toContainText(unsaved);

  const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(response.ok(), "the backend chapter must remain readable after the intentionally failed autosave").toBe(true);
  const chapter = (await response.json()) as { content: string };
  expect(
    chapter.content,
    "a rejected autosave must not mutate canonical server state behind the user's back",
  ).toContain(baseline);
  expect(chapter.content).not.toContain(unsaved);
});
