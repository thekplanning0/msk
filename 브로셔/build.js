// 사용법: NODE_PATH=$(npm root -g) node build.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage();
  await p.goto('file://' + path.resolve(__dirname, 'brochure.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.resolve(__dirname, 'THE_K_회사소개서.pdf'), preferCSSPageSize: true, printBackground: true });
  await b.close();
})();
