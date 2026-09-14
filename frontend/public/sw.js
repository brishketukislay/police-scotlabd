// Define the cache name and assets to precache
const CACHE_NAME = 'questhub-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/manifest.json',
  '/icon.svg'
];

// Install event - precache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName.startsWith('questhub-cache-') && cacheName !== CACHE_NAME;
        }).map(cacheName => caches.delete(cacheName))
      );
    })
    .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache if available, otherwise network
self.addEventListener('fetch', event => {
  // Skip cross-origin requests (like to APIs)
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached response if found
        if (response) {
          return response;
        }
        // Otherwise, try network request
        return fetch(event.request).then(
          networkResponse => {
            // Optionally, we can cache the network response for future use
            // But we'll be careful not to cache API responses or non-GET requests
            if (event.request.method === 'GET' && networkResponse.status === 200) {
              // Clone the response because it's a stream that can only be consumed once
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, responseClone);
              });
            }
            return networkResponse;
          }
        ).catch(() => {
          // If network fails, we could try to serve a fallback offline page
          // But we don't have one, so we'll just fail
          return caches.match('/'); // Try to serve the index.html from cache as a last resort
        });
      })
  );
});