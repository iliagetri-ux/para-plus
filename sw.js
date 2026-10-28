const CACHE_NAME = "para-plus-v2-23";
const ASSETS = ["./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];
self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.allSettled(ASSETS.map(path => cache.add(new Request(path, {cache:"reload"}))));
    await self.skipWaiting();
  })());
});
self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith("para-plus-") && key !== CACHE_NAME).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});
self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (req.mode === "navigate") {
    event.respondWith((async () => {
      try {
        const response = await fetch(new Request(req, {cache:"no-store"}));
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          event.waitUntil(cache.put("./index.html", response.clone()));
        }
        return response;
      } catch(err) {
        return (await caches.match("./index.html")) || Response.error();
      }
    })());
    return;
  }
  event.respondWith((async () => {
    try {
      const response = await fetch(req);
      if (response.ok) {
        const cache = await caches.open(CACHE_NAME);
        event.waitUntil(cache.put(req, response.clone()));
      }
      return response;
    } catch(err) {
      return (await caches.match(req)) || Response.error();
    }
  })());
});
