/* Syntexa AI — Service Worker PWA */
const CACHE_NAME = "syntexa-v6";
const STATIC_ASSETS = [
  "/",
  "/chat/",
  "/login/",
  "/manifest.webmanifest",
  "/LOGOTIPO.png",
  "/icon.svg",
  "/i18n/pt-BR/",
  "/i18n/en-US/",
  "/i18n/es-ES/",
  "/i18n/zh-CN/",
  "/i18n/pt-BR/chat/",
  "/i18n/en-US/chat/",
  "/i18n/es-ES/chat/",
  "/i18n/zh-CN/chat/",
  "/i18n/pt-BR/plans/",
  "/i18n/en-US/plans/",
  "/i18n/es-ES/plans/",
  "/i18n/zh-CN/plans/",
];

/* Instala e pré-cacheia os assets estáticos essenciais */
self.addEventListener("install", function (e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(STATIC_ASSETS).catch(function () {});
    })
  );
});

/* Activa e limpa TODOS os caches antigos (v1-v5) */
self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (k) { 
            return k !== CACHE_NAME || k.indexOf("syntexa-") !== -1;
          })
          .map(function (k) { 
            console.log("[SW] Deleting old cache:", k);
            return caches.delete(k); 
          })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

/* Estratégia:
   - Pedidos à API (api.syntexabr.com.br) → Network-only (nunca cacheia respostas da IA)
   - Assets _next/static → Cache-first (imutáveis com hash no nome)
   - Navegação (HTML) → Network-first, fallback para cache ou offline page
   - Resto → Stale-while-revalidate
*/
self.addEventListener("fetch", function (e) {
  var url = e.request.url;

  /* Ignorar métodos não-cacheáveis (HEAD, OPTIONS) */
  if (e.request.method !== "GET") {
    e.respondWith(fetch(e.request));
    return;
  }

  /* API — sempre directo à rede */
  if (url.indexOf("api.syntexabr.com.br") !== -1) {
    e.respondWith(fetch(e.request));
    return;
  }

  /* Assets estáticos com hash — cache-first */
  if (url.indexOf("/_next/static/") !== -1) {
    e.respondWith(
      caches.match(e.request).then(function (cached) {
        if (cached) return cached;
        return fetch(e.request).then(function (resp) {
          if (resp && resp.status === 200) {
            var clone = resp.clone();
            caches.open(CACHE_NAME).then(function (c) { c.put(e.request, clone); });
          }
          return resp;
        });
      })
    );
    return;
  }

  /* Navegação — network-only para i18n, fallback SPA para offline */
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request).then(function (resp) {
        return resp;
      }).catch(function () {
        return caches.match(e.request)
          || caches.match("/chat/")
          || caches.match("/");
      })
    );
    return;
  }

  /* Resto — stale-while-revalidate */
  e.respondWith(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.match(e.request).then(function (cached) {
        var networkFetch = fetch(e.request).then(function (resp) {
          if (resp && resp.status === 200 && resp.type === "basic") {
            try {
              cache.put(e.request, resp.clone());
            } catch (e) {}
          }
          return resp;
        }).catch(function () { return cached; });
        return cached || networkFetch;
      });
    })
  );
});
