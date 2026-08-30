import { expect, test } from "@playwright/test";
import {
  apiLogin,
  apiLogout,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

test("protected deep links survive the login round-trip instead of dumping the user on home", async ({ page, request }) => {
  const user = uniqueUser("deep-link");
  const storyTitle = `Deep Link ${Date.now()}`;

  await registerUser(request, user);
  await apiLogin(request, user);
  const storyId = await createStory(request, storyTitle);
  await apiLogout(request);

  const target = `/stories/${storyId}`;
  await page.goto(target);

  await expect(
    page,
    "an unauthenticated protected-route visit must be intercepted by the auth boundary; rendering protected UI before session validation creates a data-leak window",
  ).toHaveURL(/\/login(?:\?|$)/);

  const loginURL = new URL(page.url());
  expect(
    loginURL.searchParams.get("redirect"),
    "the router must preserve the exact protected destination; discarding it after an auth challenge breaks deep links and makes refresh/login flows lose user intent",
  ).toContain(target);

  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: /Launch Nexus/i }).click();

  await expect(
    page,
    "successful authentication must resume the protected URL that triggered login; always navigating home silently corrupts navigation state and strands users who opened bookmarks or refreshed nested routes",
  ).toHaveURL(new RegExp(`/stories/${storyId}(?:[?#]|$)`));
});

test("server-side session loss cannot leave a protected page reachable from stale frontend auth state", async ({ page, request }) => {
  const user = uniqueUser("revoked-session");
  const storyTitle = `Revoked Session ${Date.now()}`;

  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, storyTitle);
  await page.goto(`/stories/${storyId}`);
  await expect(
    page.getByRole("heading", { name: storyTitle, exact: true, level: 2 }),
  ).toBeVisible();

  await apiLogout(browserRequest);
  await page.reload();

  await expect(
    page,
    "once the backend revokes a session, a reload must not trust five-minute-old client auth cache and keep rendering private story data; server session state is authoritative",
  ).toHaveURL(/\/login(?:\?|$)/);
  await expect(
    page.getByRole("heading", { name: storyTitle, exact: true }),
    "private story content must disappear immediately after session revocation; stale protected DOM after logout is an account-boundary leak on shared machines",
  ).toHaveCount(0);
});
