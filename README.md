# mainspringhcp.com — Mainspring Healthcare Partners

Static site for Mainspring Healthcare Partners (turnaround, interim leadership, financial and
forensic analysis, marketing and agentic technology for skilled nursing and senior living). Same setup as the Kirby Gate site: content files plus
one template, assembled by `build.py`, hosted free on **GitHub Pages**, with the domain and
DNS at **Cloudflare**.

**Nothing runs on anyone's laptop.** GitHub Actions builds and deploys on every push, every
30 minutes on a schedule, and on demand from the Actions tab.

## How it works

- `content/*.html` — one file per page (body only, with a `<!--meta -->` block for
  title / description / path). A sibling `content/<name>.head.html` is injected into `<head>`
  (JSON-LD schema).
- `content/blog/*.html` — one file per article, published at `/insights/<slug>/`.
- `content/news_feeds.json` — industry headlines, refreshed automatically (see below).
- `templates/base.html` — shared header, nav, sticky CTA bar, footer.
- `assets/` — styles.css, site.js, images, the overview video. Served from `/assets/`.
- `build.py` — assembles `public/` from all of the above, plus `sitemap.xml`, `robots.txt`,
  `CNAME` and redirect stubs from the old `*.html` URLs to the clean ones.
- `public/` — the deployable site. **Never edit it, and it is not committed** — Actions
  rebuilds it every deploy. (This is the one deliberate difference from the Kirby repo,
  which does commit its output.)

```bash
python3 build.py
cd public && python3 -m http.server 8788     # preview at http://127.0.0.1:8788
```

## Publishing a change

Edit a file in `content/`, then:

```bash
git add -A && git commit -m "what changed" && git push
```

That is the whole deploy. Actions rebuilds and GitHub Pages serves it in about a minute.
You can also edit any `content/*.html` directly on github.com — the commit triggers the same
deploy, so the site can be updated from a phone.

## Industry headlines

`scripts/fetch_news_feeds.py` pulls Skilled Nursing News, Senior Housing News, Home Health
Care News and the CMS Newsroom, and writes `content/news_feeds.json`. `build.py` renders
those into `/industry/` **at build time**, so the headlines are real HTML that search engines
read — no server and no client-side fetch, which is what lets the site live on GitHub Pages.

- `deploy.yml` refreshes them before every build (every 30 minutes).
- `refresh-news-feeds.yml` commits the refreshed file once a day so the repo matches what is live.
- A feed that fails is skipped; one broken publisher never empties the page.
- McKnight's is deliberately absent — its edge returns `403` to datacenter IPs, so no CI
  runner can fetch it.

## Workflows (Actions tab → Run workflow)

| Workflow | When | What |
|---|---|---|
| Build and deploy to GitHub Pages | push to `main`, every 30 min, on demand | refresh headlines, build, deploy |
| Refresh industry headlines | daily 09:17 UTC, on demand | commit new headlines and redeploy |
| Build check | pull requests, on demand | fails if a content file breaks the build |

## One-time go-live: GitHub Pages + Cloudflare DNS

1. **The repo must be public.** Free GitHub Pages will not serve a custom domain from a
   private repo. Only the website is in here — the business files (contracts, financials,
   SOPs) are deliberately kept out.
2. **Settings → Pages → Source: GitHub Actions.** Push, and the deploy workflow publishes to
   `https://mechuz.github.io/mainspring-site/`.
3. **Settings → Pages → Custom domain:** `mainspringhcp.com` → Save. Tick **Enforce HTTPS**
   once the certificate is issued (a few minutes after DNS resolves).
4. **Cloudflare DNS** (dash.cloudflare.com → mainspringhcp.com → DNS → Records):
   - Delete the existing records that point at Cloudflare Pages.
   - Add four **A** records for `@`: `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`
   - Add a **CNAME** for `www` → `mechuz.github.io`
   - **Set every one of them to "DNS only" (grey cloud, not orange.)** Cloudflare's proxy in
     front of GitHub Pages causes certificate failures and redirect loops unless SSL/TLS mode
     is Full — grey cloud avoids the whole problem, and Pages serves HTTPS itself.
   - Leave MX and any email records alone.
5. Delete the old `mainspring` Cloudflare Pages project once the new site is confirmed live.

## Intake forms (FormSubmit — same as Kirby)

The intake form (`/contact/`), the short form on the home page and the consultant application
all post to **FormSubmit** at `admin@mainspringhcp.com`, with a copy (`_cc`) to
db@mainspringhcp.com, and send the visitor to `/thank-you/`. `site.js` submits in the
background through FormSubmit's AJAX endpoint; if that fails (service down, address not yet
activated, no network) it falls back to a pre-filled email to db@, so no enquiry is lost.

**One-time activation:** the first submission makes FormSubmit email admin@mainspringhcp.com a
confirmation link. Click it once. Until then every submission arrives by the email fallback,
which still works. After activation FormSubmit also offers a random string to use in place of
the address in the `action` URL (hides it from scrapers) — swap it into the three forms if wanted.

## Booking (Google Calendar)

`/book/` embeds a **Google Calendar appointment schedule** so a prospect can put 30 minutes on a
partner's calendar directly. To wire it: in Google Calendar (the Mainspring Workspace account)
→ Create → Appointment schedule → set the hours and a Google Meet link → Share → **Website
embed** → copy the iframe `src` → paste it into `BOOKING_URL` in `build.py` → push. Until it
is set, `/book/` shows the intake form instead, so the page never dead-ends.

## Still outstanding

- Click the FormSubmit activation email at admin@mainspringhcp.com (above).
- Paste the appointment-schedule URL into `BOOKING_URL` (above).
- **Google Search Console** — verify the domain and submit `https://mainspringhcp.com/sitemap.xml`.
