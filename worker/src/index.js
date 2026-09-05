export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const key = decodeURIComponent(url.pathname.replace(/^\/+/, ""));
    if (!key) {
      return new Response("bdr-arsiv worker", { status: 200 });
    }
    const object = await env.BUCKET.get(key);
    if (!object) {
      return new Response("Not found", { status: 404 });
    }
    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("etag", object.httpEtag);
    headers.set("Cache-Control", "public, max-age=86400");
    headers.set("Access-Control-Allow-Origin", "*");
    return new Response(object.body, { headers });
  }
};
