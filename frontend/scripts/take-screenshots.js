const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const OUT_DIR = path.join(__dirname, '..', 'out');
const SHOTS_DIR = path.join(__dirname, '..', '..', 'docs', 'screenshots');

async function takeScreenshots() {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const baseUrl = 'http://127.0.0.1:3456';

  const shots = [
    { url: `${baseUrl}/`, name: '01-home', wait: 3000 },
    { url: `${baseUrl}/chat`, name: '02-chat', wait: 2000 },
    { url: `${baseUrl}/download`, name: '03-download', wait: 2000 },
    { url: `${baseUrl}/plans`, name: '04-plans', wait: 2000 },
    { url: `${baseUrl}/educacao`, name: '05-educacao', wait: 2000 },
  ];

  for (const shot of shots) {
    try {
      await page.goto(shot.url, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(shot.wait);
      const filePath = path.join(SHOTS_DIR, `${shot.name}.png`);
      await page.screenshot({ path: filePath, fullPage: true });
      console.log(`[OK] ${shot.name}.png`);
    } catch (e) {
      console.error(`[ERR] ${shot.name}: ${e.message}`);
    }
  }

  await browser.close();
  console.log(`Screenshots saved to: ${SHOTS_DIR}`);
}

takeScreenshots().catch(console.error);
