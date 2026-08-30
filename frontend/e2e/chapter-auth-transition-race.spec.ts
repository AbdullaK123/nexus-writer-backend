import { expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  apiLogin,
  apiLogout,
  createChapter,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
  updateChapter,
} from "./helpers";

test("an in-flight chapter write from a revoked identity cannot cross into the next login", async ({ page, request }) => {
  const alice = uniqueUser("write-race-alice");
  const bob = uniqueUser("write-race-bob");
  await registerUser(request, alice);
  await registerUser(request, bob);

  await loginThroughUI(page, alice);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Alice Write Race ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Alice Pending Chapter ${Date.now()}`);
  const baseline = `ALICE-CANONICAL-${Date.now()}`;
  const pending = `ALICE-IN-FLIGHT-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  let intercepted = 0;
  let releaseWrite!: () => void;
  const mayContinue = new Promise<void>((resolve) => {
    releaseWrite = resolve;
  });

  await page.route(`**/api/chapters/${chapterId}`, async (route) => {
    if (route.request().method() !== "PUT") {
      await route.continue();
      return;
    }
    intercepted += 1;
    await mayContinue;
    await route.continue();
  });

  await page.goto(`/stories/${storyId}/${chapterId}`);
  const editor = page.locator('[contenteditable="true"]').first();
  await expect(editor).toContainText(baseline);
  await editor.fill(pending);
  await expect.poll(() => intercepted, {
    message: "Alice's autosave must be paused before her session is revoked or this test does not exercise an auth/write race",
  }).toBe(1);

  await apiLogout(browserRequest);
  await page.goto("/login");
  await page.getByLabel("Email").fill(bob.email);
  await page.getByLabel("Password").fill(bob.password);
  await page.getByRole("button", { name: /Launch Nexus/i }).click();
  await expect(page).toHaveURL(/\/$/);

  releaseWrite();
  await page.waitForTimeout(1_000);

  const bobRead = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(
    [403, 404].includes(bobRead.status()),
    "the next logged-in identity must not gain access to a resource merely because the previous identity had a mutation in flight when auth changed",
  ).toBe(true);

  await apiLogin(request, alice);
  const aliceRead = await request.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(aliceRead.ok(), "Alice's chapter must still exist so we can inspect whether the revoked in-flight write mutated it").toBe(true);
  const chapter = (await aliceRead.json()) as { content: string };

  expect(
    chapter.content,
    "a request captured under a session that was revoked before execution must fail closed; otherwise delayed browser traffic can mutate private data after the user has logged out",
  ).toContain(baseline);
  expect(chapter.content).not.toContain(pending);
});
