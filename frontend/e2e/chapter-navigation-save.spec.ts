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

test("navigating inside the autosave debounce window cannot discard chapter text", async ({ page, request }) => {
  const user = uniqueUser("navigate-unsaved");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Navigation Save ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Fast Exit ${Date.now()}`);
  const baseline = `BASELINE-${Date.now()}`;
  const unsaved = `NAVIGATION-MUST-NOT-EAT-ME-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor, "the real editor must be mounted before testing navigation against its 500ms autosave debounce").toBeVisible();
  await expect(editor).toContainText(baseline);

  await editor.fill(unsaved);
  await page.goto(`/stories/${storyId}`);
  await page.waitForTimeout(800);

  const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(response.ok(), "the chapter must remain readable after navigating away from an editor with pending local changes").toBe(true);
  const chapter = (await response.json()) as { content: string };

  expect(
    chapter.content,
    "navigation is not consent to discard prose; leaving a chapter before the debounce fires must flush or otherwise preserve the user's last edit instead of cancelling it",
  ).toContain(unsaved);
});
