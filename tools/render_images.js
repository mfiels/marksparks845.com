// Renders the typographic images from their HTML sources:
//   tools/og.html      -> src/photos/og.jpg (1200x630 link-preview card)
//   tools/favicon.html -> tools/icons/ (512px masters; process_photos.py sizes them)
//
//   npm i -D playwright && npx playwright install chromium
//   node tools/render_images.js
//   python3 tools/process_photos.py && python3 tools/build.py
const path = require("path");
const { chromium } = require("playwright");

const tools = __dirname;
const root = path.join(tools, "..");

(async () => {
  const browser = await chromium.launch();

  const og = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  await og.goto("file://" + path.join(tools, "og.html"));
  await og.evaluate(() => document.fonts.ready);
  await og.screenshot({ path: path.join(root, "src", "photos", "og.jpg"), type: "jpeg", quality: 90 });

  // Render once at 512px; process_photos.py downscales these so the letterforms stay crisp.
  const icon = await browser.newPage({ viewport: { width: 512, height: 512 } });
  for (const [query, file] of [["", "icon-512.png"], ["?square", "apple-touch-icon-512.png"]]) {
    await icon.goto("file://" + path.join(tools, "favicon.html") + query);
    await icon.evaluate(() => document.fonts.ready);
    await icon.screenshot({ path: path.join(tools, "icons", file), omitBackground: true });
  }

  await browser.close();
})();
