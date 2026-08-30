import { expect, test } from "@playwright/test";
import {
  apiLogout,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

test("an SSE reconnect that discovers a revoked session must evict private UI state", async ({ page, request, context }) => {
  const user = uniqueUser("sse-revoked");
  await registerUser(request, user);

  const firstNotificationStream = page.waitForRequest(
    (req) => req.url().includes("/api/auth/me/notifications") && req.method() === "GET",
  );

  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const privateTitle = `SSE-PRIVATE-${Date.now()}`;
  await createStory(browserRequest, privateTitle);
  await page.reload();
  await expect(page.getByRole("heading", { name: privateTitle, exact: true, level: 3 })).toBeVisible();

  await firstNotificationStream;
  await apiLogout(browserRequest);

  await context.setOffline(true);
  await expect.poll(async () => context.isOffline(), {
    message: "the browser must actually enter offline mode so the existing SSE connection is broken rather than silently remaining alive",
  }).toBe(true);
  await context.setOffline(false);

  await expect(
    page,
    "once the SSE reconnect receives a revoked-session response, auth state must be invalidated; a toast without eviction leaves private data mounted after the server has already ended the session",
  ).toHaveURL(/\/login(?:\?|$)/, { timeout: 10_000 });

  await expect(
    page.getByRole("heading", { name: privateTitle, exact: true, level: 3 }),
    "private dashboard data must disappear when the notification channel proves the session is dead; server auth state is authoritative even without a page reload",
  ).toHaveCount(0);
});
