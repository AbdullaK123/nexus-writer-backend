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

test("deleting a story cannot leave warmed descendant routes reachable from client cache", async ({ page, request }) => {
  const user = uniqueUser("story-delete-cache");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyTitle = `DELETE-TREE-${Date.now()}`;
  const chapterTitle = `DELETE-DESCENDANT-${Date.now()}`;
  const secret = `DELETED-STORY-SECRET-${Date.now()}`;
  const storyId = await createStory(browserRequest, storyTitle);
  const chapterId = await createChapter(browserRequest, storyId, chapterTitle);
  await updateChapter(browserRequest, chapterId, { content: `<p>${secret}</p>` });

  await page.goto(`/stories/${storyId}`);
  await expect(page.getByRole("heading", { name: storyTitle, exact: true })).toBeVisible();
  await page.goto(`/stories/${storyId}/${chapterId}`);
  await expect(page.getByText(secret, { exact: true })).toBeVisible();

  const deletion = await browserRequest.delete(`${API_BASE_URL}/stories/${storyId}`);
  expect(deletion.ok(), "the parent story must be deleted while its detail and chapter queries are already warm in the SPA cache").toBe(true);

  await page.locator("#back-btn").click();
  await expect(
    page,
    "navigating from a cached child to its deleted parent must revalidate existence instead of rendering the warmed story object",
  ).toHaveURL(/\/404(?:\?|$)/);
  await expect(page.getByRole("heading", { name: storyTitle, exact: true })).toHaveCount(0);
  await expect(page.getByText(secret, { exact: true })).toHaveCount(0);

  await page.goBack();
  await page.waitForTimeout(250);
  await expect(
    page.getByText(secret, { exact: true }),
    "browser history must not revive a cached chapter whose parent story has been deleted; parent deletion invalidates the entire reachable resource tree, not just the parent card",
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: chapterTitle, exact: true }),
    "deleted descendants must not leak even their metadata through warmed query state after Back navigation",
  ).toHaveCount(0);

  const childRead = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(
    childRead.status(),
    "the backend must independently prove cascade deletion or descendant invalidation; a blank frontend is not evidence that orphaned private data is gone",
  ).toBe(404);
});
