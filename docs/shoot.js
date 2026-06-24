/* Capture dashboard screenshots. Server must be running on :8008. */
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const BASE = "http://127.0.0.1:8008";
const OUT = path.join(__dirname, "screenshots");
const SAMPLE = path.join(__dirname, "..", "sample_data", "currency", "500", "reverse.jpg");

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 });
  const shot = (n) => page.screenshot({ path: path.join(OUT, n) });
  const nav = async (v) => { await page.click(`.nav-item[data-view="${v}"]`); await page.waitForTimeout(500); };

  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await shot("01-overview.png");

  // Digital arrest
  await nav("scam");
  await page.click('#scam-samples .btn[data-k="digital_arrest"]');
  await page.check("#m-ai"); await page.check("#m-spoof");
  await page.click("#scam-run");
  await page.waitForSelector("#scam-result .verdict-head", { timeout: 5000 });
  await page.waitForTimeout(500);
  await shot("02-scam.png");

  // Counterfeit
  await nav("counterfeit");
  await page.setInputFiles("#cf-file", SAMPLE);
  await page.check("#cf-uv");
  await page.fill("#cf-serial", "8AB 123456");
  await page.click("#cf-run");
  await page.waitForSelector("#cf-result .verdict-head", { timeout: 5000 });
  await page.waitForTimeout(500);
  await shot("03-counterfeit.png");

  // Fraud
  await nav("fraud");
  await page.waitForSelector("#fraud-panel .camp", { timeout: 5000 });
  await page.click("#fraud-panel .camp");
  await page.waitForTimeout(800);
  await shot("04-fraud.png");
  // Real PaySim (Kaggle) mode — capability demo (optional dataset)
  const paysimBtn = await page.$(".fsrc[data-src='paysim']");
  if (paysimBtn) {
    await paysimBtn.click();
    await page.waitForTimeout(1500);
    const hasData = await page.$("#fraud-panel .camp");
    if (hasData) await shot("11-fraud-paysim.png");
    // switch back to synthetic for any later runs
    await page.click(".fsrc[data-src='synthetic']");
    await page.waitForTimeout(800);
  }

  // Geo
  await nav("geo");
  await page.waitForSelector("#geo-panel .hot", { timeout: 5000 });
  await page.waitForTimeout(2800); // let map tiles load
  await shot("05-geo.png");
  // NCRB state stats (scroll down)
  await page.waitForSelector("#geo-states .stbar", { timeout: 5000 });
  await page.evaluate(() => document.querySelector("#geo-states").scrollIntoView({ block: "center" }));
  await page.waitForTimeout(500);
  await shot("10-geo-ncrb.png");

  // Shield
  await nav("shield");
  await page.fill("#sh-input", "A CBI officer says I am under digital arrest and must transfer all my money to an RBI verified account or be arrested today.");
  await page.click("#sh-send");
  await page.waitForTimeout(1200);
  await shot("06-shield.png");

  // Model performance (scam metrics — top of page)
  await nav("perf");
  await page.waitForSelector("#perf-kpis .perf-kpi", { timeout: 5000 });
  await page.waitForSelector("#cf-table .cfrow", { timeout: 5000 });
  await page.waitForTimeout(600);
  await shot("07-performance.png");

  // Counterfeit accuracy section (scroll down)
  await page.evaluate(() => document.querySelector("#cf-src").scrollIntoView({ block: "start" }));
  await page.waitForTimeout(500);
  await shot("08-counterfeit-accuracy.png");

  // Audit ledger section
  await page.waitForSelector("#audit-table .aud", { timeout: 5000 });
  await page.evaluate(() => document.querySelector("#audit-status").scrollIntoView({ block: "start" }));
  await page.waitForTimeout(400);
  await shot("09-audit-ledger.png");

  await browser.close();
  console.log("Screenshots written to", OUT);
})().catch(e => { console.error(e); process.exit(1); });
