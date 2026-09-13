"""Generate static homepage links from .github/FUNDING.yml (requires PyYAML)."""
from html import escape
from pathlib import Path
from urllib.parse import quote
import argparse
import yaml

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    'github': ('GitHub Sponsors', 'https://github.com/sponsors/'),
    'ko_fi': ('Ko-fi', 'https://ko-fi.com/'),
    'liberapay': ('Liberapay', 'https://liberapay.com/'),
    'buy_me_a_coffee': ('Buy Me a Coffee', 'https://buymeacoffee.com/'),
    'thanks_dev': ('thanks.dev', 'https://thanks.dev/u/gh/'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if links need regeneration')
    args = parser.parse_args()
    funding = yaml.safe_load((ROOT / '.github/FUNDING.yml').read_text())
    unknown = [key for key, value in funding.items() if value and key not in PLATFORMS]
    if unknown:
        parser.error(f'Add URL mappings for new funding platforms: {unknown}')
    primary, secondary = [], []
    for key, (label, base) in PLATFORMS.items():
        accounts = funding.get(key)
        if not accounts:
            continue
        if not isinstance(accounts, list):
            accounts = [accounts]
        for account in accounts:
            if not isinstance(account, str) or not account.strip():
                parser.error(f'Expected a nonempty username for {key}')
            url = escape(base + quote(account.strip(), safe=''), quote=True)
            label_text = label if len(accounts) == 1 else f'{label} · {account}'
            css = 'cta primary' if key == 'github' else 'cta ghost' if key == 'ko_fi' else 'funding-link'
            link = f'<a class="{css}" href="{url}" target="_blank" rel="noopener noreferrer">{escape(label_text)} <span aria-hidden="true">↗</span></a>'
            (primary if key in ('github', 'ko_fi') else secondary).append(link)
    lines = ['        ' + link for link in primary]
    if secondary:
        lines += ['        <div class="funding-alternatives" aria-label="More ways to contribute">']
        lines += ['          ' + link for link in secondary]
        lines += ['        </div>']
    page = ROOT / 'index.html'
    original = page.read_text()
    start, end = '<!-- funding-links:start -->', '<!-- funding-links:end -->'
    assert original.count(start) == original.count(end) == 1
    before, rest = original.split(start)
    _, after = rest.split(end)
    updated = before + start + '\n' + '\n'.join(lines) + '\n        ' + end + after
    if args.check:
        if updated != original:
            parser.error('Funding links are stale; run python3 scripts/sync_funding.py')
        print('Funding links match .github/FUNDING.yml')
    else:
        page.write_text(updated)


if __name__ == '__main__':
    main()
