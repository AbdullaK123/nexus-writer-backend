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

test("an offline autosave must preserve local text and resume when connectivity returns", async ({ page, request, context }) => {
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

  let putRequests = 0;
  page.on("request", (req) => {
    if (req.method() === "PUT" && req.url().endsWith(`/api/chapters/${chapterId}`)) {
      putRequests += 1;
    }
  });

  await context.setOffline(true);
  await editor.fill(offlineEdit);
  await page.waitForTimeout(700);

  expect(
    putRequests,
    "TanStack Query's online network mode must pause the autosave while the browser is offline; firing a doomed request instead defeats its reconnect semantics",
  ).toBe(0);

  await expect(
    editor,
    "going offline must not roll the editor back to stale server text; the local buffer is the only surviving copy of the writer's work",
  ).toContainText(offlineEdit);

  await context.setOffline(false);

  await expect.poll(() => putRequests, {
    message: "the paused autosave must resume once connectivity returns instead of abandoning the writer's queued edit",
    timeout: 10_000,
  }).toBe(1);

  await expect.poll(async () => {
    const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
    if (!response.ok()) return "";
    return ((await response.json()) as { content: string }).content;
  }, {
    message: "once connectivity returns, the resumed autosave must persist the local buffer; otherwise UI and canonical server state remain permanently divergent",
    timeout: 15_000,
  }).toContain(offlineEdit);
});
