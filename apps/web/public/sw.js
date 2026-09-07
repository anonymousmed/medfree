/* MEDFREE service worker — PWA/offline support (Step 18).
 *
 * Strategy:
 *  - App shell & static assets: cache-first (content is versioned by Next hash).
 *  - Navigation requests: network-first with offline shell fallback.
 *  - API calls (/api/*): NOT prefetched/cached (data must stay fresh & correct;
 *    we never serve stale medical content offline). The shell fallback shows a
 *    friendly offline message instead of breaking navigation.
 */
const VERSION = "medfree-v1";
const SHELL_CACHE = `${VERSION}-shell`;
const OFFLINE_URL = "/offline.html";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) =>
      cache.addAll(["/", OFFLINE_URL, "/manifest.webmanifest", "/icon-192.svg", "/icon-512.svg"])
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Never intercept or cache API calls — correctness over offline convenience.
  if (request.url.includes("/api/")) return;

  // Navigations: network-first, fall back to stale shell, then offline page.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Static assets: cache-first with network fill.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          if (response.ok && request.url.startsWith(self.location.origin)) {
            const copy = response.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(OFFLINE_URL));
    })
  );
});
