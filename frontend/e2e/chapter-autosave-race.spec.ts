import { expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

test("an older autosave arriving late cannot overwrite the user's newer chapter text", async ({ page, request }) => {
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
    message: "the first debounced autosave must actually leave the browser before we manufacture an out-of-order arrival",
  }).toBe(1);

  await editor.fill(newer);
  await expect.poll(() => putRequests, {
    message: "the newer edit must produce a second write while the older write is still delayed; otherwise this is not testing the race",
  }).toBe(2);

  await expect.poll(() => putResponses, {
    message: "both competing autosaves must finish before canonical server state is inspected",
    timeout: 10_000,
  }).toBe(2);

  const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(response.ok(), "the canonical chapter must remain readable after competing autosaves").toBe(true);
  const chapter = (await response.json()) as { content: string };

  expect(
    chapter.content,
    "network reordering is normal in production; an older request that arrives late must never erase keystrokes the user made afterward",
  ).toContain(newer);
  expect(
    chapter.content,
    "the stale autosave payload must not become canonical merely because its HTTP request completed last",
  ).not.toContain(older);
});
