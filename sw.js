// 테마 브리프 service worker: 앱 화면은 캐시로 빠르게, 뉴스(data.json)는 항상 최신 우선
const CACHE = 'theme-brief-v1';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return; // 폰트 등 외부 요청은 그대로

  // 뉴스 데이터·앱 화면: 네트워크 우선, 오프라인이면 마지막 저장본
  if (url.pathname.endsWith('data.json') || e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request).then(r => r || caches.match('index.html')))
    );
    return;
  }
  // 아이콘 등: 캐시 우선
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
