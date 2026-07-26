// sw.js — offline-first service worker for Hearth
const CACHE = 'hearth-v1';
const ASSETS = [
  './',
  './index.html',
  './css/styles.css',
  './manifest.webmanifest',
  './js/app.js',
  './js/store.js',
  './js/router.js',
  './js/nav.js',
  './js/utils.js',
  './js/ui.js',
  './js/views/parts.js',
  './js/views/dashboard.js',
  './js/views/money.js',
  './js/views/plan.js',
  './js/views/household.js',
  './js/views/goals.js',
  './js/views/settings.js',
  './js/views/onboarding.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS).catch(() => {})).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const { request } = e;
  if (request.method !== 'GET') return;
  // network-first for navigation, cache-first for assets
  if (request.mode === 'navigate') {
    e.respondWith(fetch(request).catch(() => caches.match('./index.html')));
    return;
  }
  e.respondWith(
    caches.match(request).then(cached => cached || fetch(request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(request, copy)).catch(() => {});
      return res;
    }).catch(() => cached))
  );
});
