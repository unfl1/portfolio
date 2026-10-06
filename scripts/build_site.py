"""Package the independently edited index.html for GitHub Pages.

Edit README.md for the GitHub document and index.html for the website.
This script never generates website content from README.md or rewrites index.html.
It refreshes asset versions only in the deployment copy under _site/.
"""
from pathlib import Path
import hashlib
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / '_site'


def version_asset(match):
    attribute, asset = match.groups()
    asset_path = ROOT / asset
    if not asset_path.is_file():
        raise ValueError(f'Missing website asset: {asset}')
    version = hashlib.sha256(asset_path.read_bytes()).hexdigest()[:12]
    return f'{attribute}="{asset}?v={version}"'


def build():
    page = (ROOT / 'index.html').read_text(encoding='utf-8')
    page = re.sub(
        r'(src|href|data-image)="(assets/[^"?]+)(?:\?v=[a-f0-9]+)?"',
        version_asset,
        page,
    )
    OUTPUT.mkdir(exist_ok=True)
    shutil.copytree(ROOT / 'assets', OUTPUT / 'assets', dirs_exist_ok=True)
    shutil.copyfile(ROOT / '.nojekyll', OUTPUT / '.nojekyll')
    (OUTPUT / 'index.html').write_text(page, encoding='utf-8')
    print('Packaged index.html and assets into _site/ (README.md is independent).')


if __name__ == '__main__':
    build()
