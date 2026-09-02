// Samachar Service Worker — Offline Reading & Asset Cache
const CACHE_NAME = 'samachar-cache-v2.6';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/home.html',
  '/latest.html',
  '/factcheck.html',
  '/bookmarks.html',
  '/profile.html',
  '/about.html',
  '/login.html',
  '/register.html',
  '/assets/css/variables.css',
  '/assets/css/layout.css',
  '/assets/css/style.css',
  '/assets/js/api.js',
  '/assets/js/layout.js',
  '/assets/js/app.js',
  '/assets/icons/favicon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  
  // Cache-first strategy for static assets, network-first for API
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});
