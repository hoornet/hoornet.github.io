"""Run with python3 tests/check_csp.py; requires Brave or Chromium on PATH."""
import base64
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import argparse

ROOT = Path(__file__).resolve().parents[1]
BROWSER = next((shutil.which(name) for name in
                ('brave-origin', 'brave', 'brave-browser', 'chromium')
                if shutil.which(name)), None)
options = argparse.ArgumentParser(description=__doc__)
options.add_argument('--browser', default=BROWSER, help='Browser executable path or name')
BROWSER = options.parse_args().browser
assert BROWSER, 'Install Brave or Chromium to run browser checks'


class PolicyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policy = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            assert self.policy is None, 'Duplicate policy'
            self.policy = attrs['content']
        if tag in {'script', 'style', 'link', 'img'}:
            assert self.policy, 'Policy must precede resources'


def browser(path, profile):
    result = subprocess.run(
        [BROWSER, '--headless', '--no-sandbox', '--disable-gpu', '--timeout=5000',
         f'--user-data-dir={profile}', '--dump-dom', str(path)],
        capture_output=True, text=True, timeout=30, check=True)
    assert '<html' in result.stdout
    return result.stdout


with tempfile.TemporaryDirectory(prefix='hoornet-csp-') as tmp:
    tmp = Path(tmp)
    control = tmp / 'control.html'
    control.write_text('<html><body><script>document.body.dataset.injected="yes"</script></body></html>')
    assert 'data-injected="yes"' in browser(control.as_uri(), tmp / 'profile')
    count = 0
    for page in ROOT.rglob('*.html'):
        source = page.read_text()
        if '<head>' not in source:
            continue
        parser = PolicyParser()
        parser.feed(source)
        directives = dict(part.strip().split(' ', 1)
                          for part in parser.policy.split(';'))
        assert directives['default-src'] == "'none'"
        assert directives['base-uri'] == "'none'"
        assert directives['form-action'] == "'none'"
        assert 'unsafe-inline' not in directives['script-src']
        for script in re.findall(r'<script>(.*?)</script>', source, re.S):
            digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
            assert f"'sha256-{digest}'" == directives['script-src']
        # Two injection classes: inline script and inline event handler.
        attack = ('<script>document.body.dataset.injected="yes"</script>'
                  '<img src="missing.png" onerror="document.body.dataset.injected=\'yes\'">')
        fixture = tmp / 'attack.html'
        injected, replacements = re.subn(r'(<body\b[^>]*>)',
                                        lambda m: m[0] + attack, source, count=1)
        assert replacements == 1, page
        fixture.write_text(injected)
        dom = browser(fixture.as_uri(), tmp / 'profile')
        assert 'data-injected="yes"' not in dom, page
        count += 1
    # The exact allowed script must still redirect both legacy fragments.
    for name in ('index.html', 'privacy.html', 'terms.html'):
        shutil.copyfile(ROOT / name, tmp / name)
    for fragment in ('privacy', 'terms'):
        expected = re.search(r'<title>(.*?)</title>', (ROOT / f'{fragment}.html').read_text())[0]
        dom = browser((tmp / 'index.html').as_uri() + '#' + fragment, tmp / 'profile')
        assert expected in dom, fragment
    assert (ROOT / 'google4a0977d0dca7ae27.html').read_text().strip() == 'google-site-verification: google4a0977d0dca7ae27.html'
    print(f'PASS: {count} early policies, blocked script/event injections, both legacy redirects, verification token')
