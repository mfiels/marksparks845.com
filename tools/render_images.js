// Renders the typographic images:
//   tools/og.html               -> src/photos/og.jpg (1200x630 link-preview card)
//   tools/icons/icon.svg         -> tools/icons/icon-512.png (rounded tile)
//   tools/icons/apple-touch-icon.svg -> tools/icons/apple-touch-icon-512.png (square)
//
//   python3 tools/make_mark.py        # regenerate the M⚡S SVGs from the font (optional)
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
  await og.waitForSelector("body[data-ready]");
  await og.screenshot({ path: path.join(root, "src", "photos", "og.jpg"), type: "jpeg", quality: 90 });

  const icon = await browser.newPage({ viewport: { width: 512, height: 512 } });
  for (const [svg, png] of [["icon.svg", "icon-512.png"], ["apple-touch-icon.svg", "apple-touch-icon-512.png"]]) {
    await icon.goto("file://" + path.join(tools, "icons", svg));
    await icon.screenshot({ path: path.join(tools, "icons", png), omitBackground: true });
  }

  await browser.close();
})();
