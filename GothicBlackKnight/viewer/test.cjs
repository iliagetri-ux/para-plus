const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert');
(async () => {
  const root = path.resolve(__dirname, '..');
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_BIN || '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--disable-crash-reporter', '--disable-crashpad', '--disable-breakpad', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route('http://knight.local/**', async route => {
      let filename = path.resolve(root, '.' + decodeURIComponent(new URL(route.request().url()).pathname));
      if (!filename.startsWith(root + path.sep)) return route.abort();
      if (fs.existsSync(filename) && fs.statSync(filename).isDirectory()) filename = path.join(filename, 'index.html');
      if (!fs.existsSync(filename)) return route.fulfill({ status: 404, body: 'Not found' });
      const types = { '.html': 'text/html', '.glb': 'model/gltf-binary', '.png': 'image/png' };
      await route.fulfill({ status: 200, contentType: types[path.extname(filename)] || 'application/octet-stream', body: fs.readFileSync(filename) });
    });
    await page.goto('http://knight.local/viewer/');
    await page.waitForFunction(() => window.viewerDiagnostics?.ready, null, { timeout: 60000 });
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(root, 'artifacts/WebGL_Mobile_Preview.png'), timeout: 60000 });
    const canvas = page.locator('canvas');
    const digest = async () => crypto.createHash('sha256').update(await canvas.screenshot()).digest('hex');
    const frame = () => page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const original = await digest();
    const cdp = await page.context().newCDPSession(page);
    const touch = (type, points) => cdp.send('Input.dispatchTouchEvent', {type, touchPoints:points.map(([id,x,y])=>({id,x,y}))});
    await touch('touchStart', [[1,215,480]]);
    for (let k=1;k<=6;k++) await touch('touchMove',[[1,215+k*12,480]]);
    await touch('touchEnd', []);await frame();
    assert.notStrictEqual(await digest(), original, 'Touch drag did not change the rendered view');
    await page.locator('#reset').click();await frame();
    assert.strictEqual(await digest(), original, 'Reset did not restore the view');
    await touch('touchStart', [[1,160,480],[2,270,480]]);
    for (let k=1;k<=5;k++) await touch('touchMove',[[1,160-k*10,480],[2,270+k*10,480]]);
    await touch('touchEnd', []);await frame();
    assert.notStrictEqual(await digest(), original, 'Pinch did not change the rendered view');
    await page.locator('#reset').click();await frame();
    const result = await page.evaluate(() => window.viewerDiagnostics);
    result.interactions = {touch_orbit:true, pinch_zoom:true, reset:true};
    result.pageErrors = errors;
    result.viewport = { width: 430, height: 932 };
    result.browser = 'Chromium headless SwiftShader; mobile viewport, not physical iPhone';
    fs.writeFileSync(path.join(root, 'artifacts/webgl_check.json'), JSON.stringify(result, null, 2));
    console.log(result);
    if (errors.length || result.errors.length) process.exitCode = 1;
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
