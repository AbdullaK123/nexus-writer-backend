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

test("a stale editor tab cannot silently destroy a newer committed chapter revision", async ({ page, request, context }) => {
  const user = uniqueUser("two-tab-conflict");
  await registerUser(request, user);
  await loginThroughUI(page, user);
  await expect(page).toHaveURL(/\/$/);

  const browserRequest = page.context().request;
  const storyId = await createStory(browserRequest, `Two Tab Conflict ${Date.now()}`);
  const chapterId = await createChapter(browserRequest, storyId, `Shared Chapter ${Date.now()}`);
  const baseline = `SHARED-BASELINE-${Date.now()}`;
  const tabAEdit = `${baseline} TAB-A-COMMITTED-${Date.now()}`;
  const tabBEdit = `${baseline} TAB-B-STALE-${Date.now()}`;
  await updateChapter(browserRequest, chapterId, { content: `<p>${baseline}</p>` });

  const baselineResponse = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(baselineResponse.ok()).toBe(true);
  const baselineChapter = (await baselineResponse.json()) as { revision?: string };
  expect(
    baselineChapter.revision,
    "chapter reads must expose an exact revision token or stale-tab protection cannot distinguish old editors from current ones",
  ).toBeTruthy();

  const pageB = await context.newPage();
  await Promise.all([
    page.goto(`/stories/${storyId}/${chapterId}`),
    pageB.goto(`/stories/${storyId}/${chapterId}`),
  ]);

  const editorA = page.locator('[contenteditable="true"]').first();
  const editorB = pageB.locator('[contenteditable="true"]').first();
  await expect(editorA).toContainText(baseline);
  await expect(editorB).toContainText(baseline);

  const writeA = page.waitForResponse(
    (response) => response.request().method() === "PUT" && response.url().endsWith(`/api/chapters/${chapterId}`),
  );
  await editorA.fill(tabAEdit);
  const responseA = await writeA;
  const requestAPayload = responseA.request().postDataJSON() as { expectedRevision?: string };
  expect(
    requestAPayload.expectedRevision,
    "the first editor write must carry the exact revision it loaded; a missing or mutated token makes optimistic concurrency either inert or self-conflicting",
  ).toBe(baselineChapter.revision);

  const responseABody = await responseA.text();
  expect(
    responseA.ok(),
    `tab A must successfully commit the newer server revision before stale tab B attempts its write; status=${responseA.status()} body=${responseABody}`,
  ).toBe(true);

  await expect.poll(async () => {
    const response = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
    if (!response.ok()) return "";
    return ((await response.json()) as { content: string }).content;
  }, {
    message: "tab A's edit must be canonical before the stale tab is allowed to attack it",
  }).toContain("TAB-A-COMMITTED");

  const writeB = pageB.waitForResponse(
    (response) => response.request().method() === "PUT" && response.url().endsWith(`/api/chapters/${chapterId}`),
  );
  await editorB.fill(tabBEdit);
  const responseB = await writeB;

  const canonicalResponse = await browserRequest.get(`${API_BASE_URL}/chapters/${chapterId}`);
  expect(canonicalResponse.ok()).toBe(true);
  const canonical = ((await canonicalResponse.json()) as { content: string }).content;

  const staleWriteRejected = responseB.status() === 409 || responseB.status() === 412;
  const mergePreservedBoth = canonical.includes("TAB-A-COMMITTED") && canonical.includes("TAB-B-STALE");

  expect(
    staleWriteRejected || mergePreservedBoth,
    "a stale editor instance must not silently overwrite text already committed by another tab; reject the stale revision or merge both edits, because undetected lost updates are data corruption",
  ).toBe(true);

  if (staleWriteRejected) {
    expect(
      canonical,
      "rejecting the stale tab is only safe if the newer committed revision remains canonical",
    ).toContain("TAB-A-COMMITTED");
    await expect(
      editorB,
      "a conflict response must preserve tab B's local buffer so the writer can recover or reconcile it manually",
    ).toContainText("TAB-B-STALE");
  }
});
