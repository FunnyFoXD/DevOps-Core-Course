function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    console.log("edge-request", {
      path: url.pathname,
      colo: request.cf?.colo,
      country: request.cf?.country,
    });

    if (url.pathname === "/health") {
      return json({ status: "ok" });
    }

    if (url.pathname === "/" || url.pathname === "") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        message: "Hello from Cloudflare Workers",
        timestamp: new Date().toISOString(),
      });
    }

    if (url.pathname === "/deployment") {
      return json({
        app: env.APP_NAME,
        course: env.COURSE_NAME,
        version: env.WORKER_VERSION,
        runtime: "cloudflare-workers",
        timestamp: new Date().toISOString(),
        note: "This endpoint summarizes deployment metadata from plaintext vars in wrangler.jsonc. Secrets are stored separately and are not included here.",
      });
    }

    if (url.pathname === "/edge") {
      const cf = request.cf;
      return json({
        colo: cf?.colo,
        country: cf?.country,
        city: cf?.city,
        asn: cf?.asn,
        httpProtocol: cf?.httpProtocol,
        tlsVersion: cf?.tlsVersion,
      });
    }

    if (url.pathname === "/counter") {
      const raw = await env.SETTINGS.get("visits");
      const visits = Number(raw ?? "0") + 1;
      await env.SETTINGS.put("visits", String(visits));
      return json({ visits, key: "visits" });
    }

    if (url.pathname === "/config") {
      return json({
        plaintextVars: {
          APP_NAME: env.APP_NAME,
          COURSE_NAME: env.COURSE_NAME,
          WORKER_VERSION: env.WORKER_VERSION,
        },
        secretsConfigured: {
          API_TOKEN: Boolean(env.API_TOKEN),
          ADMIN_EMAIL: Boolean(env.ADMIN_EMAIL),
        },
        kv: { binding: "SETTINGS" },
        whyPlaintextVarsAreNotForSecrets:
          "wrangler vars are stored in your repo and worker configuration, appear in the Cloudflare dashboard, and can be read by anyone with access to the project. Use `wrangler secret put` for API tokens, passwords, and other sensitive values.",
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
