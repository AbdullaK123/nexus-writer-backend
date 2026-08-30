import { expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

test("an older autosave cannot be overtaken by a newer chapter write", async ({ page, request }) => {
  const user = uniqueUser("autosave-race");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Autosave Race ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Race Chapter ${Date.now()}`);

  let putResponses = 0;
  page.on("response", (response) => {
    if (response.request().method() === "PUT" && response.url().endsWith(`/api/chapters/${chapterId}`)) {
      putResponses += 1;
    }
  });

  let putRequests = 0;
  await page.route(`**/api/chapters/${chapterId}`, async (route) => {
    if (route.request().method() !== "PUT") {
      await route.continue();
      return;
    }

    putRequests += 1;
    if (putRequests === 1) {
      await new Promise((resolve) => setTimeout(resolve, 1_500));
    }
    await route.continue();
  });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor, "the real Tiptap editor must be mounted before we attack autosave ordering").toBeVisible();

  const older = `OLDER-${Date.now()}`;
  const newer = `NEWER-${Date.now()}`;

  await editor.fill(older);
  await expect.poll(() => putRequests, {
    message: "the first debounced autosave must leave the browser before the second edit is made",
  }).toBe(1);

  await editor.fill(newer);
  await page.waitForTimeout(700);
  expect(
    putRequests,
    "chapter writes must remain serialized while the older autosave is in flight; sending the newer request concurrently allows the network to invert user intent",
  ).toBe(1);

  await expect.poll(() => putResponses, {
    message: "the first autosave must finish before the queued newer write can start",
    timeout: 10_000,
  }).toBeGreaterThanOrEqual(1);
  await expect.poll(() => putRequests, {
    message: "the newer autosave must be sent after the older write settles rather than being dropped",
    timeout: 10_000,
  }).toBe(2);
  await expect.poll(() => putResponses, {
    message: "both ordered autosaves must finish before canonical server state is inspected",
    timeout: 10_000,
  }).toBe(2);

  const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(response.ok(), "the canonical chapter must remain readable after queued autosaves").toBe(true);
  const chapter = (await response.json()) as { content: string };

  expect(
    chapter.content,
    "the last edit in user-intent order must become canonical even when the preceding request is artificially delayed",
  ).toContain(newer);
  expect(
    chapter.content,
    "the older autosave must not remain canonical after the queued newer edit completes",
  ).not.toContain(older);
});
