// Headless browser E2E against the live stack (frontend :3000 + backend :5000).
import { chromium } from "playwright";

const BASE = "http://localhost:3000";
const email = `e2e_${Date.now()}@test.com`;
let pass = 0;
let fail = 0;
const errors = [];

function check(name, cond, extra = "") {
  if (cond) {
    pass++;
    console.log(`  PASS  ${name}`);
  } else {
    fail++;
    console.log(`  FAIL  ${name}  ${extra}`);
  }
}

const browser = await chromium.launch();
const page = await browser.newPage();
page.on("console", (m) => {
  if (m.type() === "error") errors.push(`console.error: ${m.text()}`);
});
page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));

try {
  // 1. Guard: unauthenticated root redirects to /login
  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  check("guard redirects to /login", page.url().includes("/login"), page.url());

  // 2. Register a new account
  await page.getByText("Crear cuenta", { exact: true }).click();
  await page.getByPlaceholder("tu@email.com").fill(email);
  await page.getByPlaceholder("••••••••").fill("password123");
  await page.getByRole("button", { name: "Registrarme" }).click();

  // 3. Lands on stations page with the seeded universe
  await page.waitForURL((u) => !u.toString().includes("/login"), { timeout: 15000 });
  await page.waitForSelector(".station-card", { timeout: 15000 });
  const cards = await page.locator(".station-card").count();
  check("stations page shows 4 seeded stations", cards === 4, `got ${cards}`);
  check(
    "universe summary rendered",
    await page.getByText("Universo Narrativo Compartido").isVisible(),
  );

  // 4. Navigate to News via sidebar -> seeded news render
  await page.getByRole("link", { name: /Noticias/ }).click();
  await page.waitForURL((u) => u.toString().includes("/news"), { timeout: 10000 });
  await page.waitForTimeout(1200);
  const newsCards = await page.locator(".news-card").count();
  check("news page shows seeded news", newsCards >= 3, `got ${newsCards}`);

  // 5. Back to stations and generate an episode end-to-end
  await page.getByRole("link", { name: /Estaciones/ }).click();
  await page.waitForSelector(".station-card", { timeout: 10000 });
  await page.locator(".station-card .btn-primary").first().click();

  // Pipeline modal opens
  await page.waitForSelector(".modal-card", { timeout: 10000 });
  check("generation pipeline modal opened", await page.locator(".modal-card").isVisible());

  // Wait for completion (worker processes it) -> "Ver episodio" button appears
  await page.getByRole("button", { name: /Ver episodio/ }).waitFor({ timeout: 120000 });
  check("episode generation completed", true);
  await page.getByRole("button", { name: /Ver episodio/ }).click();

  // 6. Episodes page shows the new episode
  await page.waitForURL((u) => u.toString().includes("/episodes"), { timeout: 10000 });
  await page.waitForTimeout(1500);
  const epRows = await page.locator(".episode-row, .episode-item, [data-episode]").count();
  check("episodes page lists at least one episode", epRows >= 1, `got ${epRows}`);

  check("no uncaught runtime errors", errors.length === 0, errors.join(" | "));
} catch (e) {
  fail++;
  console.log(`  FAIL  exception: ${e.message}`);
  if (errors.length) console.log("  console/page errors:\n   " + errors.join("\n   "));
} finally {
  await browser.close();
}

console.log(`\n==== E2E RESULT: ${pass} passed, ${fail} failed ====`);
process.exit(fail ? 1 : 0);
