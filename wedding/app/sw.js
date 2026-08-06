/* John & Emma's Wedding — offline cache
   Network-first for the page itself, so a deployed change is never hidden
   behind a stale cache; cache-first only for the icons, which never change. */
var CACHE = "je-wedding-v11";
var ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-maskable-512.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ASSETS); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== CACHE) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isPage(req) {
  return req.mode === "navigate" ||
         (req.headers.get("accept") || "").indexOf("text/html") !== -1;
}

self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;

  /* the page: always try the network, fall back to cache when offline */
  if (isPage(e.request)) {
    e.respondWith(
      fetch(e.request).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put("./index.html", copy); });
        }
        return res;
      }).catch(function () {
        return caches.match("./index.html", { ignoreSearch: true })
          .then(function (hit) { return hit || caches.match("./"); });
      })
    );
    return;
  }

  /* everything else: serve from cache, refresh it in the background */
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(function (hit) {
      var net = fetch(e.request).then(function (res) {
        if (res && res.ok && new URL(e.request.url).origin === location.origin) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
        }
        return res;
      }).catch(function () { return hit; });
      return hit || net;
    })
  );
});
