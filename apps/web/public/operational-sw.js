/* Cache only public UI shells/assets. API reads and all commands always use the network. */
const CACHE = "rodada-operational-shell-v1";
const shell = url => url.origin === self.location.origin && (
  /^\/(bar|kitchen|manage)(\/|$)/.test(url.pathname) ||
  /^\/guest\/[^/]+$/.test(url.pathname) ||
  (url.pathname === "/" && /^(bar|cozinha|gerencia|cliente)\.rodada\.ai$/.test(url.hostname))
);
const asset = url => url.origin === self.location.origin && (
  url.pathname.startsWith("/_next/static/") || url.pathname.startsWith("/fonts/")
);
self.addEventListener("install", event => event.waitUntil(self.skipWaiting()));
self.addEventListener("activate", event => event.waitUntil(self.clients.claim()));
async function remember(request, response) {
  if (!response.ok || response.redirected) return;
  const cache = await caches.open(CACHE);
  await cache.put(request, response.clone());
  const keys = await cache.keys();
  for (const key of keys.slice(0, Math.max(0, keys.length - 200))) await cache.delete(key);
}
self.addEventListener("message", event => {
  if (event.data?.type !== "CACHE_OPERATIONAL_SHELL") return;
  event.waitUntil(Promise.all((event.data.urls || []).slice(0, 100).map(async value => {
    const url = new URL(value, self.location.origin);
    if (!shell(url) && !asset(url)) return;
    try { const response = await fetch(url, { headers: { Accept: "text/html,*/*" } }); await remember(url.href, response); } catch { }
  })));
});
self.addEventListener("fetch", event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== "GET" || !(asset(url) || (request.mode === "navigate" && shell(url)))) return;
  event.respondWith((async () => {
    const cached = await caches.match(request);
    if (asset(url) && cached) return cached;
    try {
      const response = await fetch(request);
      event.waitUntil(remember(request, response));
      return response;
    } catch (error) { if (cached) return cached; throw error; }
  })());
});
