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

test("a valid chapter cannot be mounted under the wrong parent story", async ({ page, request }) => {
  const user = uniqueUser("nested-mismatch");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyA = await createStory(browserRequest, `Story A ${Date.now()}`);
  const storyB = await createStory(browserRequest, `Story B ${Date.now()}`);
  const chapterTitle = `A-ONLY-CHAPTER-${Date.now()}`;
  const secret = `A-ONLY-CONTENT-${Date.now()}`;
  const chapterA = await createChapter(browserRequest, storyA, chapterTitle);
  await updateChapter(browserRequest, chapterA, { content: `<p>${secret}</p>` });

  let childFetches = 0;
  page.on("request", (request) => {
    if (request.method() === "GET" && request.url().includes(`/api/chapters/${chapterA}`)) {
      childFetches += 1;
    }
  });

  await page.goto(`/stories/${storyB}/${chapterA}`);
  await expect(page).toHaveURL(/\/404(?:\?|$)/);

  expect(
    childFetches,
    "the parent story's chapter list already proves this child does not belong here; fetching the unrelated chapter anyway creates a transient confused-deputy data leak",
  ).toBe(0);
  await expect(
    page.getByText(secret, { exact: true }),
    "valid child IDs are not enough: rendering a chapter from story A inside story B creates a fake resource hierarchy",
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: chapterTitle, exact: true }),
    "the chapter title itself must not leak through a mismatched parent route",
  ).toHaveCount(0);
});

test("another account cannot open a chapter by guessing its nested URL", async ({ page, request }) => {
  const alice = uniqueUser("nested-alice");
  const bob = uniqueUser("nested-bob");
  await registerUser(request, alice);
  await registerUser(request, bob);

  await loginThroughUI(page, alice);
  await expect(page).toHaveURL(/\/$/);
  const browserRequest = page.context().request;
  const aliceStory = await createStory(browserRequest, `Alice Private ${Date.now()}`);
  const chapterTitle = `ALICE-PRIVATE-CHAPTER-${Date.now()}`;
  const chapterId = await createChapter(browserRequest, aliceStory, chapterTitle);

  await apiLogout(browserRequest);
  await page.goto("/login");
  await page.getByLabel("Email").fill(bob.email);
  await page.getByLabel("Password").fill(bob.password);
  await page.getByRole("button", { name: /Launch Nexus/i }).click();
  await expect(page).toHaveURL(/\/$/);

  await page.goto(`/stories/${aliceStory}/${chapterId}`);
  await expect(page).toHaveURL(/\/404(?:\?|$)/);
  await expect(
    page.getByRole("heading", { name: chapterTitle, exact: true }),
    "a guessed nested URL must never reveal another account's chapter; client routing cannot weaken the backend ownership boundary",
  ).toHaveCount(0);
});
