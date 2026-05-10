#!/usr/bin/env python3
"""
Bremen Abfahrten — Cloud Server für Railway
Läuft als öffentlicher Webserver, kein lokales Setup nötig.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import socket
import json
import os
import sys
from pathlib import Path

# Railway setzt PORT als Umgebungsvariable
PORT = int(os.environ.get('PORT', 8000))
HAFAS_URL = 'https://fahrplaner.vbn.de/bin/mgate.exe'
TIMEOUT = 15

MANIFEST = json.dumps({
    "name": "Bremen Abfahrten",
    "short_name": "Abfahrten",
    "description": "Live BSAG/VBN Abfahrtszeiten für Bremen",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0b0f17",
    "theme_color": "#0b0f17",
    "orientation": "portrait-primary",
    "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}]
}, ensure_ascii=False)

ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="100" fill="#0b0f17"/>
  <rect x="60" y="60" width="392" height="392" rx="80" fill="#ffcc00"/>
  <text x="256" y="340" font-family="Arial Black,Arial" font-weight="900"
        font-size="280" text-anchor="middle" fill="#0b0f17">B</text>
</svg>'''

SERVICE_WORKER = r"""
const CACHE = 'bremen-v2';
const SHELL = ['/'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks =>
    Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith('/api/') || url.hostname !== self.location.hostname) {
    e.respondWith(fetch(e.request));
    return;
  }
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
      return res;
    }))
  );
});
"""

class Handler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path != '/api/mgate':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(length)
            req = urllib.request.Request(
                HAFAS_URL, data=post_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'bremen-abfahrten-cloud/2.0'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as up:
                body = up.read()
                status = up.status
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.URLError as e:
            self._err(502, f'HAFAS nicht erreichbar: {e}')
        except Exception as e:
            self._err(500, f'Fehler: {e}')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._serve_file('index.html', 'text/html; charset=utf-8')
        elif self.path == '/manifest.json':
            self._serve_bytes(MANIFEST.encode(), 'application/manifest+json')
        elif self.path == '/icon.svg':
            self._serve_bytes(ICON_SVG.encode(), 'image/svg+xml')
        elif self.path == '/sw.js':
            self._serve_bytes(SERVICE_WORKER.encode(), 'application/javascript', no_cache=True)
        elif self.path == '/ip':
            # On cloud: return the public hostname
            host = os.environ.get('RAILWAY_PUBLIC_DOMAIN', self.headers.get('Host', 'localhost'))
            body = json.dumps({'ip': host, 'port': 443, 'cloud': True}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, 'Not found')

    def _serve_file(self, filename, content_type):
        path = Path(__file__).parent / filename
        if not path.exists():
            self.send_error(404, f'{filename} not found')
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(data)

    def _serve_bytes(self, data, content_type, no_cache=False):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        if no_cache:
            self.send_header('Cache-Control', 'no-cache')
        else:
            self.send_header('Cache-Control', 'max-age=86400')
        self.end_headers()
        self.wfile.write(data)

    def _err(self, code, msg):
        body = json.dumps({'error': True, 'message': msg}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        msg = fmt % args
        if any(x in msg for x in ['/favicon', '/sw.js', '/manifest', '/icon', '304']):
            return
        print(f'  · {msg}', flush=True)


def main():
    os.chdir(Path(__file__).parent)
    socketserver.TCPServer.allow_reuse_address = True
    is_cloud = bool(os.environ.get('RAILWAY_PUBLIC_DOMAIN'))
    try:
        with socketserver.TCPServer(('', PORT), Handler) as httpd:
            if is_cloud:
                domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', f'localhost:{PORT}')
                print(f'\n  🚊  Bremen Abfahrten läuft auf Railway!')
                print(f'      https://{domain}\n', flush=True)
            else:
                print(f'\n  🚊  Bremen Abfahrten läuft lokal auf:')
                print(f'      http://localhost:{PORT}\n', flush=True)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n  Gestoppt. 👋\n')


if __name__ == '__main__':
    main()
