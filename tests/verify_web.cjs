// Run with Playwright installed (or NODE_PATH set). WEBGL_ANGLE=swiftshader selects software rendering.
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {createServer} = require('node:http');
const {createReadStream, statSync, mkdirSync, writeFileSync} = require('node:fs');
const {resolve, extname, basename, sep} = require('node:path');
(async () => {
  const root = resolve(__dirname, '../dist/web');
  const output = resolve(__dirname, 'artifacts');
  mkdirSync(output, {recursive: true});
  const server = createServer((req, res) => {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/\/$/, '/index.html');
    const path = resolve(root, '.' + pathname);
    if (!path.startsWith(root + sep)) { res.writeHead(403).end(); return; }
    try {
      const size = statSync(path).size;
      const type = {'.mjs':'text/javascript','.html':'text/html','.json':'application/json','.wasm':'application/wasm'}[extname(path)];
      res.writeHead(200, {'Content-Type':type || 'application/octet-stream','Content-Length':size});
      createReadStream(path).pipe(res);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  let browser;
  try {
    browser = await chromium.launch({channel: process.env.WEBGL_BROWSER || 'msedge', headless: true,
      args: [...(process.env.WEBGL_COLD ? ['--disable-gpu-shader-disk-cache'] : []), ...(process.env.WEBGL_ANGLE ? [`--use-angle=${process.env.WEBGL_ANGLE}`] : [])]});
    const page = await browser.newPage({viewport:{width:960,height:540}});
    const errors = [];
    page.on('console', msg => { console.log(msg.type(), msg.text()); if (msg.type() === 'error') errors.push(msg.text()); });
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      globalThis.renderContextLosses = 0;
      document.addEventListener('webglcontextlost', e => {
        if (e.target.parentElement?.id === 'surfaces') globalThis.renderContextLosses++;
      }, true);
    });
    await page.goto(`http://127.0.0.1:${server.address().port}/?autorun=0`);
    await page.waitForFunction(() => window.aquarius, null, {timeout:120000});
    await page.evaluate(() => {
      window.aquarius.run('tests/capture_web.aqua').catch(e => console.error(e.message));
    });
    await page.waitForSelector('#surfaces canvas', {timeout:120000});
    const renderer = await page.evaluate(() => {
      const gl = document.querySelector('#surfaces canvas').getContext('webgl2');
      const debug = gl.getExtension('WEBGL_debug_renderer_info');
      return debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    });
    console.log('GPU', renderer);
    await page.waitForFunction(() => ['finished','error'].includes(window.aquarius.state), null, {timeout:180000});
    const result = await page.evaluate(() => ({state:window.aquarius.state,
      error:document.querySelector('#error').textContent, lost:globalThis.renderContextLosses,
      shots:globalThis.__aquaFilamentScreenshots || []}));
    assert.equal(result.state, 'finished', result.error);
    assert.equal(result.lost, 0, 'The rendering canvas lost its WebGL context');
    assert.deepEqual(errors, []);
    assert.equal(result.shots.length, 5, 'All five scenes, including Bistro, must render');
    for (const shot of result.shots) {
      const bytes = Buffer.from(shot.url.split(',')[1], 'base64');
      assert(bytes.length > 10000, `Blank or missing scene: ${shot.path}`);
      writeFileSync(resolve(output, basename(shot.path)), bytes);
    }
    assert.match(await page.locator('#output').textContent(), /SHOWCASE_WEB_CAPTURE_OK/);
    if (process.env.REQUIRE_RENDERER) assert.match(renderer, new RegExp(process.env.REQUIRE_RENDERER, 'i'));
    const report = {passed:true, browser:process.env.WEBGL_BROWSER || 'msedge', angle:process.env.WEBGL_ANGLE || 'default',
      coldShaderCache:!!process.env.WEBGL_COLD, renderer, contextLosses:result.lost, captures:result.shots.map(s => basename(s.path)), errors};
    const reportFile = process.env.WEBGL_REPORT || resolve(output, 'browser-validation.json');
    mkdirSync(resolve(reportFile, '..'), {recursive:true});
    writeFileSync(reportFile, JSON.stringify(report, null, 2) + '\n');
    console.log('PASS: all five web scenes rendered without a lost context or console error');
  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise(r => server.close(r));
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
