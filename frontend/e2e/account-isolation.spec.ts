import { expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  apiLogout,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

test("switching identities cannot resurrect the previous account's cached story data", async ({ page, request }) => {
  const alice = uniqueUser("alice");
  const bob = uniqueUser("bob");
  const aliceOnlyTitle = `ALICE-ONLY-${Date.now()}`;

  await registerUser(request, alice);
  await registerUser(request, bob);

  await loginThroughUI(page, alice);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  await createStory(browserRequest, aliceOnlyTitle);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: aliceOnlyTitle, exact: true, level: 3 }),
  ).toBeVisible();

  await apiLogout(browserRequest);
  await page.goto("/login");

  await page.getByLabel("Email").fill(bob.email);
  await page.getByLabel("Password").fill(bob.password);
  await page.getByRole("button", { name: /Launch Nexus/i }).click();
  await expect(page).toHaveURL(/\/$/);

  await expect(
    page.getByRole("heading", { name: aliceOnlyTitle, exact: true, level: 3 }),
    "TanStack Query cache must be identity-scoped in practice, not just on the backend; showing account A's cached story after account B logs in is a direct cross-account confidentiality breach",
  ).toHaveCount(0);

  const storiesResponse = await browserRequest.get(`${API_BASE_URL}/stories`);
  expect(
    storiesResponse.ok(),
    "the second account must still have a valid backend session; otherwise a blank dashboard could falsely make the cache-isolation assertion look safe",
  ).toBe(true);
  const body = (await storiesResponse.json()) as { stories: Array<{ title: string }> };
  expect(
    body.stories.some((story) => story.title === aliceOnlyTitle),
    "the backend must independently prove account B cannot see account A's story; frontend absence alone is not evidence of authorization safety",
  ).toBe(false);
});
