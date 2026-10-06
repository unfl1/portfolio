"""Build the static portfolio from README.md using only Python's standard library."""
from pathlib import Path
import html
import re
import struct
import hashlib

ROOT = Path(__file__).resolve().parent.parent

# Website wording is managed separately so README.md remains unchanged.
WEB_COPY_REPLACEMENTS = {
    '수락한 약속이 10개일 때 SQL 22회, 50개일 때 102회, 100개일 때 202회 실행되어 목록 크기에 따라 조회가 반복되는 문제 재현.':
    '수락한 약속이 10개일 때 SQL 22회, 50개일 때 102회, 100개일 때 202회가 실행되어, 약속 수에 따라 조회 횟수가 늘어나는 것을 확인.',
}

def inline(value):
    for original, revised in WEB_COPY_REPLACEMENTS.items():
        value = value.replace(original, revised)
    value = html.escape(value)
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
    value = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1 ↗</a>', value)
    return value.replace('&lt;br&gt;', '<br>')

def markdown(value):
    out = []
    listing = table = False
    for line in value.strip().splitlines():
        line = line.strip()
        if listing and not line.startswith('- '):
            out.append('</ul>'); listing = False
        if table and not line.startswith('|'):
            out.append('</table></div>'); table = False
        if not line or line == '<br>':
            continue
        image = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if image:
            alt, path = image.groups()
            if not (ROOT / path).is_file():
                raise ValueError(f'Missing image: {path}')
            # Reserve diagram space before lazy loading so anchor targets stay put.
            dimensions = ''
            if Path(path).suffix.lower() == '.png':
                with (ROOT / path).open('rb') as image_file:
                    header = image_file.read(24)
                if header[:8] != b'\x89PNG\r\n\x1a\n':
                    raise ValueError(f'Invalid PNG: {path}')
                width, height = struct.unpack('>II', header[16:24])
                dimensions = f' width="{width}" height="{height}"'
            version = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]
            image_url = html.escape(f'{path}?v={version}')
            artwork = f'<img src="{image_url}" alt="{html.escape(alt)}"{dimensions} loading="lazy">'
            out.append(f'<button class="diagram" type="button" data-image="{image_url}" aria-label="{html.escape(alt)} 크게 보기">{artwork}<span class="zoom-hint">그림 크게 보기 <span aria-hidden="true">↗</span></span></button>')
        elif line.startswith('- '):
            if not listing:
                out.append('<ul>'); listing = True
            out.append('<li>' + inline(line[2:]) + '</li>')
        elif line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', cell) for cell in cells):
                continue
            tag = 'td' if table else 'th'
            if not table:
                out.append('<div class="table-scroll"><table>'); table = True
            out.append('<tr>' + ''.join(f'<{tag}>{inline(cell)}</{tag}>' for cell in cells) + '</tr>')
        elif line.startswith('#'):
            out.append('<h4>' + inline(line.lstrip('#').strip()) + '</h4>')
        else:
            out.append('<p>' + inline(line) + '</p>')
    if listing: out.append('</ul>')
    if table: out.append('</table></div>')
    return ''.join(out)

CONFIG = [
    dict(id='jiki', name='Jiki', role='백엔드 개발, 팀장', repository='https://github.com/CapstoneDesign-timeisgold/Back'),
    dict(id='dajoba', name='다잡아', role='프론트엔드 개발', repository='https://github.com/TABA-DaJobA/Front'),
    dict(id='mylibrary', name='나만의 도서관', role='프론트엔드와 백엔드 개발, 배포 환경 구축', repository='https://github.com/unfl1/mylibrary'),
]

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
sections = re.split(r'^# (Jiki|다잡아|나만의 도서관)\s*$', readme, flags=re.M)
sources = dict(zip(sections[1::2], sections[2::2]))
projects = []
for item in CONFIG:
    source = sources[item['name']]
    tech = re.search(r'^\*\*기술\*\*:\s*(.*?)<br>', source, re.M).group(1)
    architecture = re.search(r'## 시스템 구조\s*(.*?)\n## 핵심 기능', source, re.S).group(1)
    features = re.search(r'## 핵심 기능\s*(.*?)(?=\n## )', source, re.S).group(1)
    cases = list(re.finditer(r'^### (\d+)\. ([^\n]+)\n(.*?)(?=^### |^## 근거 자료|\Z)', source, re.M | re.S))
    issue_html = []
    for case in cases:
        number, title, body = case.groups()
        groups = list(re.finditer(r'^#### ([^\n]+)\n(.*?)(?=^#### |\Z)', body, re.M | re.S))
        contents = []
        for group in groups:
            label, text = group.groups()
            is_diagram = bool(re.search(r'!\[[^\]]*\]\([^)]+\)', text))
            heading = '' if is_diagram else '<h4>' + inline(label) + '</h4>'
            contents.append('<section class="case-block">' + heading + markdown(text) + '</section>')
        issue_html.append(f'<article class="case"><h3>{inline(number + ". " + title)}</h3><div class="case-content">{"".join(contents)}</div></article>')
    evidence = re.search(r'^## 근거 자료\s*(.*?)(?=^# |\Z)', source, re.M | re.S)
    resources = '<div class="resources"><h3>코드와 설계 기록</h3>' + markdown(evidence.group(1)) + '</div>' if evidence else ''
    description = re.search(r'^\*\*(.*?)\*\*\s*$', source, re.M).group(1)
    projects.append(f'''<section class="project-section" id="{item['id']}" aria-labelledby="{item['id']}-title"><div class="project-heading"><h2 id="{item['id']}-title">{item['name']}</h2><p class="project-description">{inline(description)}</p><dl class="project-meta"><div><dt>담당 역할</dt><dd>{item['role']}</dd></div><div><dt>기술</dt><dd>{inline(tech)}</dd></div><div><dt>저장소</dt><dd><a href="{item['repository']}" target="_blank" rel="noopener noreferrer">GitHub ↗</a></dd></div></dl></div><div class="project-body"><section class="architecture"><h3>시스템 구조</h3>{markdown(architecture)}</section><section class="features"><h3>핵심 기능</h3>{markdown(features)}</section><section class="cases"><h3 class="cases-heading">{'배포 환경 구축' if item['id'] == 'mylibrary' else '사용자 경험 개선' if item['id'] == 'dajoba' else '문제 해결'}</h3>{''.join(issue_html)}</section>{resources}</div></section>''')

page = '''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="강현준의 개발 포트폴리오. Jiki 백엔드의 정산 정합성과 성능 개선, 다잡아 프론트엔드의 사용자 경험, 나만의 도서관의 클라우드 배포 기록.">
<meta name="theme-color" content="#ffffff"><title>강현준 | 개발 포트폴리오</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body><a class="skip-link" href="#main">본문으로 이동</a><header class="site-header"><div class="scroll-progress" aria-hidden="true"><span></span></div><div class="header-inner"><a class="brand" href="#top">강현준</a><nav aria-label="프로젝트 바로가기"><a href="#jiki">Jiki</a><a href="#dajoba">다잡아</a><a href="#mylibrary">나만의 도서관</a></nav><a class="github-link" href="https://github.com/unfl1" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div></header>
<main id="main" class="wrap"><section class="introduction" id="top"><h1>강현준 개발 포트폴리오</h1></section><div class="project-list">__PROJECTS__</div></main>
<footer class="site-footer wrap"><span>강현준</span><a href="#top">맨 위로 ↑</a></footer>
<dialog id="image-dialog" aria-label="구조도 크게 보기"><div class="dialog-toolbar"><span id="image-caption">구조도</span><button id="close-dialog" type="button" aria-label="이미지 닫기">닫기 <span aria-hidden="true">×</span></button></div><div class="dialog-image"><img id="dialog-img" alt=""></div></dialog></body></html>'''
page = page.replace('__PROJECTS__', ''.join(projects))
# A new URL on every asset change prevents previously cached styles/scripts being reused.
for asset in ('assets/site.css', 'assets/site.js'):
    version = hashlib.sha256((ROOT / asset).read_bytes()).hexdigest()[:12]
    page = page.replace(f'"{asset}"', f'"{asset}?v={version}"')
(ROOT / 'index.html').write_text(page, encoding='utf-8')
print(f'Built index.html: {len(CONFIG)} projects, {sum(len(re.findall(r"^### ", source, re.M)) for source in sources.values())} cases.')
