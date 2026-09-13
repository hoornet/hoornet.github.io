# hoornet.github.io

## Homepage and funding

The featured apps, open-source projects, and other apps/services share one static
homepage. Open-source labels are based on the linked repositories' licenses.

The sponsorship panel's links come from `.github/FUNDING.yml`. After editing
funding accounts, run `python3 scripts/sync_funding.py` and commit the updated
`index.html` too. The helper requires PyYAML (`python3 -m pip install PyYAML`);
the published site has no build or JavaScript dependency for funding links.
Run `python3 scripts/sync_funding.py --check` to detect stale links. Add a URL
mapping in the helper when enabling a new funding platform.

Keep these app-linked legal URLs stable; do not move or rename their files:

- `https://hoornet.github.io/astro93/privacy.html`
- `https://hoornet.github.io/astro93/terms.html`
- `https://hoornet.github.io/calm-dog/privacy.html`
- `https://hoornet.github.io/calm-dog/terms.html`

## Content Security Policy

GitHub Pages serves this static site. Each HTML page declares an enforcing CSP
immediately after its charset declaration, before any resources or scripts.
The policy blocks scripts by default; the home page permits only the SHA-256
hash of its existing legacy privacy/terms redirect script. If that script changes
(including whitespace), update its CSP hash. Existing inline CSS, local styles,
Google Fonts, and local/data images remain allowed.

Run `python3 tests/check_csp.py` to check policy placement, script hashes,
script/event-handler injection blocking, and both legacy redirects in headless
Brave Origin (or Brave/Chromium). Tests use a temporary browser profile.
Use `python3 tests/check_csp.py --browser chromium` to select Chromium explicitly.

The Google site-verification file must retain its exact verification content.
The separately hosted `/tinnitus-notch/` project is outside this repository.

**Hosting limitation:** a meta policy does not set an HTTP response header.
GitHub Pages has no custom response-header configuration, so this mitigation
does not close a scanner finding that specifically requires the
`Content-Security-Policy` header. Full remediation requires a custom domain and
a host or reverse proxy that can set that header. Serve each page's policy as
the response header there, adding `frame-ancestors 'none'` (which is unsupported
in meta policies). Do not add `_headers` or server configuration files expecting
GitHub Pages to apply them.

After deployment, check the response with `curl -sSI https://hoornet.github.io/`.
Only consider the missing-header finding resolved when the affected response
actually includes an enforcing `Content-Security-Policy` header.
