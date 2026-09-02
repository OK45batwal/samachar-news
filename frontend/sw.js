// Samachar Service Worker — Auto Flush Cache for Development
const CACHE_NAME = 'samachar-cache-v3.0';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Network-only fetch during active development
self.addEventListener('fetch', (event) => {
  return;
});
