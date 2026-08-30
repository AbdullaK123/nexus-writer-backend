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

test("an offline autosave failure must preserve local text and recover after connectivity returns", async ({ page, request, context }) => {
  const user = uniqueUser("offline-autosave");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Offline Save ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Offline Chapter ${Date.now()}`);
  const baseline = `ONLINE-BASELINE-${Date.now()}`;
  const offlineEdit = `OFFLINE-EDIT-MUST-SURVIVE-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor).toContainText(baseline);

  const failedWrite = page.waitForEvent("requestfailed", {
    predicate: (req) => req.method() === "PUT" && req.url().endsWith(`/api/chapters/${chapterId}`),
  });
  await context.setOffline(true);
  await editor.fill(offlineEdit);
  await failedWrite;

  await expect(
    editor,
    "losing the network during autosave must not roll the editor back to stale server text; the local buffer is the only surviving copy of the writer's work",
  ).toContainText(offlineEdit);

  await context.setOffline(false);

  await expect.poll(async () => {
    const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
    if (!response.ok()) return "";
    return ((await response.json()) as { content: string }).content;
  }, {
    message: "once connectivity returns, an autosave-only editor must eventually persist the unsaved local buffer; silently abandoning the failed write leaves the UI and canonical server state permanently divergent",
    timeout: 15_000,
  }).toContain(offlineEdit);
});
