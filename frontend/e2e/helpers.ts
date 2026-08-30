import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const API_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api";

export type TestUser = {
  username: string;
  email: string;
  password: string;
};

export function uniqueUser(prefix: string): TestUser {
  const nonce = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return {
    username: `${prefix}-${nonce}`.slice(0, 90),
    email: `${prefix}-${nonce}@example.com`,
    password: "ValidPassword!123",
  };
}

async function requireOk(response: Awaited<ReturnType<APIRequestContext["post"]>>, context: string) {
  if (!response.ok()) {
    throw new Error(`${context} failed with ${response.status()}: ${await response.text()}`);
  }
  return response;
}

export async function registerUser(request: APIRequestContext, user: TestUser): Promise<void> {
  await requireOk(
    await request.post(`${API_BASE_URL}/auth/register`, { data: user }),
    "register test user",
  );
}

export async function apiLogin(request: APIRequestContext, user: TestUser): Promise<void> {
  await requireOk(
    await request.post(`${API_BASE_URL}/auth/login`, {
      data: { email: user.email, password: user.password },
    }),
    "API login",
  );
}

export async function apiLogout(request: APIRequestContext): Promise<void> {
  await requireOk(
    await request.post(`${API_BASE_URL}/auth/logout`),
    "API logout",
  );
}

export async function createStory(request: APIRequestContext, title: string): Promise<string> {
  await requireOk(
    await request.post(`${API_BASE_URL}/stories`, { data: { title } }),
    "create story",
  );

  const response = await requireOk(
    await request.get(`${API_BASE_URL}/stories`),
    "list stories after create",
  );
  const body = (await response.json()) as {
    stories: Array<{ storyId: string; title: string }>;
  };
  const story = body.stories.find((item) => item.title === title);
  if (!story) {
    throw new Error(`Created story ${JSON.stringify(title)} was not returned by the real backend.`);
  }
  return story.storyId;
}

export async function createChapter(
  request: APIRequestContext,
  storyId: string,
  title: string,
): Promise<string> {
  const response = await requireOk(
    await request.post(`${API_BASE_URL}/stories/${storyId}/chapters`, { data: { title } }),
    "create chapter",
  );
  const chapter = (await response.json()) as { id: string };
  if (!chapter.id) {
    throw new Error("create chapter succeeded but the backend returned no chapter id");
  }
  return chapter.id;
}

export async function updateChapter(
  request: APIRequestContext,
  chapterId: string,
  payload: { title?: string; content?: string; published?: boolean },
): Promise<void> {
  await requireOk(
    await request.put(`${API_BASE_URL}/chapters/${chapterId}`, { data: payload }),
    "update chapter",
  );
}

export async function loginThroughUI(page: Page, user: TestUser): Promise<void> {
  await page.goto("/login");
  await expect(
    page.getByLabel("Email"),
    "the login route must render before the test can authenticate; a global error page here means browser-to-backend auth probing failed before the behavior under test",
  ).toBeVisible({ timeout: 5_000 });
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: /Launch Nexus/i }).click();
}
