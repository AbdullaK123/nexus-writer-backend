import { expect, test } from "@playwright/test";
import {
  apiLogout,
  createStory,
  loginThroughUI,
  registerUser,
  uniqueUser,
} from "./helpers";

const isNotificationStream = (url: string) => url.includes("/api/auth/me/notifications");

test("an SSE reconnect that discovers a revoked session must evict private UI state", async ({ page, request, context }) => {
  const user = uniqueUser("sse-revoked");
  await registerUser(request, user);

  const activeStream = page.waitForRequest(
    (req) => isNotificationStream(req.url()) && req.method() === "GET",
  );
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);
  await activeStream;

  const browserRequest = page.context().request;
  const privateTitle = `SSE-PRIVATE-${Date.now()}`;
  await createStory(browserRequest, privateTitle);
  await page.reload();
  await expect(page.getByRole("heading", { name: privateTitle, exact: true, level: 3 })).toBeVisible();

  await apiLogout(browserRequest);

  const failedStream = page.waitForEvent("requestfailed", {
    predicate: (req) => isNotificationStream(req.url()) && req.method() === "GET",
  });
  await context.setOffline(true);
  await failedStream;

  const rejectedReconnect = page.waitForResponse(
    (response) =>
      isNotificationStream(response.url()) &&
      response.request().method() === "GET" &&
      (response.status() === 401 || response.status() === 403),
  );
  await context.setOffline(false);
  await rejectedReconnect;

  await expect(
    page,
    "once the SSE reconnect receives a revoked-session response, auth state must be invalidated; a toast without eviction leaves private data mounted after the server has already ended the session",
  ).toHaveURL(/\/login(?:\?|$)/, { timeout: 10_000 });

  await expect(
    page.getByRole("heading", { name: privateTitle, exact: true, level: 3 }),
    "private dashboard data must disappear when the notification channel proves the session is dead; server auth state is authoritative even without a page reload",
  ).toHaveCount(0);
});
