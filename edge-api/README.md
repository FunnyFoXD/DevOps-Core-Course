# edge-api (Lab 17)

Cloudflare Workers TypeScript API for the DevOps Core Course lab on edge deployment.

## Prerequisites

- Node.js 18+
- A Cloudflare account and [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/) (`npm install` adds it locally)

## One-time setup

1. Install dependencies:

   ```bash
   cd edge-api
   npm install
   ```

2. Log in to Cloudflare:

   ```bash
   npx wrangler login
   npx wrangler whoami
   ```

3. Create a KV namespace and put its **id** into `wrangler.jsonc` (replace `REPLACE_WITH_KV_NAMESPACE_ID`):

   ```bash
   npx wrangler kv namespace create SETTINGS
   ```

4. Create **two** secrets (values are not stored in git):

   ```bash
   npx wrangler secret put API_TOKEN
   npx wrangler secret put ADMIN_EMAIL
   ```

   For local `wrangler dev`, you can copy `.dev.vars.example` to `.dev.vars` and edit (`.dev.vars` is gitignored).

5. Deploy:

   ```bash
   npx wrangler deploy
   ```

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | App info (uses plaintext `vars`) |
| GET | `/health` | Health check |
| GET | `/deployment` | Deployment metadata (JSON) |
| GET | `/edge` | Edge request metadata (`request.cf`) |
| GET | `/counter` | KV-backed visit counter |
| GET | `/config` | Public config + why vars ≠ secrets |

## Useful commands

```bash
npx wrangler dev
npx wrangler tail
npx wrangler deployments list
npx wrangler rollback
```

Public URL shape: `https://edge-api.<your-subdomain>.workers.dev` (actual subdomain is shown after deploy).

See [WORKERS.md](./WORKERS.md) for lab write-up, evidence placeholders, and Kubernetes comparison.
