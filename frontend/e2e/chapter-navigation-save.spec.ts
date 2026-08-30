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
  const storyTitle = `Navigation Save ${Date.now()}`;
  const storyId = await createStory(browserRequest, storyTitle);
  const chapterId = await createChapter(browserRequest, storyId, `Fast Exit ${Date.now()}`);
  const baseline = `BASELINE-${Date.now()}`;
  const unsaved = `NAVIGATION-MUST-NOT-EAT-ME-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor, "the real editor must be mounted before testing navigation against its 500ms autosave debounce").toBeVisible();
  await expect(editor).toContainText(baseline);

  await editor.fill(unsaved);
  await page.getByRole("button", { name: `← ${storyTitle}`, exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/stories/${storyId}/?$`));

  await expect.poll(async () => {
    const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
    if (!response.ok()) return "";
    return ((await response.json()) as { content: string }).content;
  }, {
    message: "SPA navigation is not consent to discard prose; leaving a chapter before the debounce fires must flush the pending autosave and make the last edit canonical",
    timeout: 10_000,
  }).toContain(unsaved);
});
