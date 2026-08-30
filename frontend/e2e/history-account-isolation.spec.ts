import { expect, test } from "@playwright/test";
import {
  apiLogout,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
  updateChapter,
} from "./helpers";

test("browser history cannot resurrect a previous account's private chapter DOM", async ({ page, request }) => {
  const alice = uniqueUser("history-alice");
  const bob = uniqueUser("history-bob");
  await registerUser(request, alice);
  await registerUser(request, bob);

  await loginThroughUI(page, alice);
  await expect(page).toHaveURL(/\/$/);
  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Alice History Story ${Date.now()}`);
  const chapterTitle = `ALICE-HISTORY-CHAPTER-${Date.now()}`;
  const secret = `ALICE-HISTORY-SECRET-${Date.now()}`;
  const chapterId = await createChapter(browserRequest, storyId, chapterTitle);
  await updateChapter(browserRequest, chapterId, { content: `<p>${secret}</p>` });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  await expect(page.getByText(secret, { exact: true })).toBeVisible();

  await apiLogout(browserRequest);
  await page.goto("/login");
  await page.getByLabel("Email").fill(bob.email);
  await page.getByLabel("Password").fill(bob.password);
  await page.getByRole("button", { name: /Launch Nexus/i }).click();
  await expect(page).toHaveURL(/\/$/);

  for (let i = 0; i < 2; i += 1) {
    await page.goBack();
    await page.waitForTimeout(150);
    await expect(
      page.getByText(secret, { exact: true }),
      "Back navigation after an identity switch must never restore account A's cached private editor DOM inside account B's session; browser history is not an authorization boundary",
    ).toHaveCount(0);
  }

  await page.goForward();
  await page.waitForTimeout(150);
  await expect(
    page.getByText(secret, { exact: true }),
    "Forward navigation must be just as incapable of reviving private DOM from the prior identity",
  ).toHaveCount(0);

  await page.goto(`/stories/${storyId}/${chapterId}`);
  await expect(page).toHaveURL(/\/404(?:\?|$)/);
  await expect(
    page.getByRole("heading", { name: chapterTitle, exact: true }),
    "a stale history entry and a direct guessed URL must converge on the same ownership boundary; neither may reveal the previous account's chapter metadata",
  ).toHaveCount(0);
});
