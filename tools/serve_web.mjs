// Serve the web export locally and open a separate Edge profile using the browser default backend.
// Usage: node tools/serve_web.mjs [--port=8765] [--no-open]
import {createServer} from 'node:http';
import {createReadStream, existsSync, mkdirSync, statSync} from 'node:fs';
import {dirname, extname, resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';

const project = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const root = resolve(project, 'dist/web');
const portOption = process.argv.find(a => a.startsWith('--port='));
const port = portOption ? Number(portOption.slice(7)) : 8765;
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Invalid port');
if (!existsSync(resolve(root, 'program.json'))) throw new Error('Build first: aqua build . --target web -o dist/web');
const types = {'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm'};
const server = createServer((request, response) => {
  let path;
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname).replace(/\/$/, '/index.html');
    path = resolve(root, '.' + pathname);
    if (!path.startsWith(root + sep)) { response.writeHead(403).end(); return; }
    const size = statSync(path).size;
    response.writeHead(200, {'Content-Type':types[extname(path)] || 'application/octet-stream', 'Content-Length':size, 'Cache-Control':'no-cache'});
    createReadStream(path).on('error', () => response.destroy()).pipe(response);
  } catch { response.writeHead(404).end(); }
});
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
server.listen(port, '127.0.0.1', () => {
  const url = `http://127.0.0.1:${server.address().port}/`;
  console.log(`Filament showcase: ${url}\nPress Ctrl+C to stop the server.`);
  if (process.argv.includes('--no-open')) return;
  const edge = [process.env['ProgramFiles(x86)'], process.env.ProgramFiles]
    .filter(Boolean).map(p => resolve(p, 'Microsoft/Edge/Application/msedge.exe')).find(existsSync);
  if (!edge) { console.log('Microsoft Edge was not found. Open the URL in a browser with a working WebGL backend.'); return; }
  const profile = resolve(project, 'dist/edge-showcase-profile');
  mkdirSync(profile, {recursive:true});
  const browser = spawn(edge, [`--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', '--new-window', url],
    {detached:true, windowsHide:true, stdio:'ignore'});
  browser.on('error', error => console.error(`Cannot open Edge: ${error.message}`));
  browser.unref();
});
const stop = () => { server.closeAllConnections(); server.close(); };
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
