const BACKEND = "https://api.syntexabr.com.br";

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const target = BACKEND + url.pathname + url.search;
  const req = context.request;

  if (req.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With, Accept",
      },
    });
  }

  const headers = new Headers(req.headers);
  headers.delete("host");

  const resp = await fetch(target, {
    method: req.method,
    headers,
    body: req.method !== "GET" && req.method !== "HEAD" ? req.body : undefined,
    redirect: "manual",
  });

  const respHeaders = new Headers(resp.headers);
  respHeaders.set("Access-Control-Allow-Origin", "*");

  return new Response(resp.body, { status: resp.status, headers: respHeaders });
}
