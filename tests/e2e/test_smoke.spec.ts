import { test, expect } from "@playwright/test";

test("login form renders and dashboard requires auth", async ({ page }) => {
  // /dashboard/ unauthenticated redirects to login
  const r = await page.goto("/dashboard/");
  expect(r?.status()).toBeLessThan(400);
  await expect(page).toHaveURL(/\/auth\/login\//);
});

test("/healthz returns 200 with status ok", async ({ request }) => {
  const r = await request.get("/healthz");
  expect(r.status()).toBe(200);
  expect(await r.json()).toMatchObject({ status: "ok" });
});

test("/design-system/ renders in dev", async ({ page }) => {
  await page.goto("/design-system/");
  await expect(page.getByRole("heading", { name: /design system/i })).toBeVisible();
  await expect(page.getByText(/buttons/i)).toBeVisible();
});
