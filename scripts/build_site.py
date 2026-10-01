"""Build the static portfolio from README.md using only Python's standard library."""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parent.parent

def inline(value):
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
            out.append(f'<button class="diagram" type="button" data-image="{html.escape(path)}" aria-label="{html.escape(alt)} 크게 보기"><img src="{html.escape(path)}" alt="{html.escape(alt)}" loading="lazy"><span>그림 크게 보기 <span aria-hidden="true">↗</span></span></button>')
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
    dict(id='jiki', name='Jiki', number='01', category='BACKEND', role='백엔드 개발 · 팀장', summary='약속을 지키는 서비스, 흔들리지 않는 정산.', description='참여 상태와 도착 여부에 따라 벌금과 보상을 정산하는 서비스.', accent='blue', repository='https://github.com/CapstoneDesign-timeisgold/Back', image='assets/jiki/jiki-architecture.png', outcome='202 → 2', outcome_label='약속 100개 조회 SQL', highlights=['참여 마감과 정산의 충돌 방지', '동시 정산 정합성과 재시도 처리', '목록 조회 SQL과 응답 시간 개선']),
    dict(id='dajoba', name='다잡아', number='02', category='FRONTEND', role='프론트엔드 개발', summary='사용자가 기다리고, 탐색하고, 작성하는 경험.', description='자기소개서를 분석하고 채용공고와 연결하는 AI 매칭 서비스.', accent='green', repository='https://github.com/TABA-DaJobA/Front', image='assets/dajoba/dajoba-architecture.png', outcome='20건', outcome_label='페이지당 공고 조회 범위', highlights=['서버 페이지네이션과 탐색 위치 표시', '분석 대기 상태의 시각적 안내', '자기소개서 초안 자동 저장과 복원']),
    dict(id='mylibrary', name='나만의 도서관', number='03', category='FULLSTACK & CLOUD', role='프론트엔드 · 백엔드 · 배포 환경 구축', summary='서비스 구현에서 컨테이너 배포와 운영까지.', description='도서 공유 서비스를 만들고 클라우드 배포 환경을 구성한 프로젝트.', accent='orange', repository='https://github.com/unfl1/mylibrary', image='assets/mylibrary/system-overview.png', outcome='Docker → K8s', outcome_label='컨테이너 기반 배포', highlights=['Docker 이미지와 Kubernetes 배포', 'GitHub Webhook과 Jenkins 빌드', 'k6 부하 테스트와 수동 Pod 확장']),
]

readme = (ROOT / 'README.md').read_text(encoding='utf-8')
sections = re.split(r'^# (Jiki|다잡아|나만의 도서관)\s*$', readme, flags=re.M)
sources = dict(zip(sections[1::2], sections[2::2]))
cards = []
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
            label = {'전체적인 아키텍처': '처리 흐름', '구성': '처리 흐름', '수행 구성': '처리 흐름'}.get(label, label)
            contents.append('<section class="case-block"><h4>' + inline(label) + '</h4>' + markdown(text) + '</section>')
        issue_html.append(f'<details class="case"><summary><span class="case-number">{number.zfill(2)}</span><h3>{inline(title)}</h3><span class="expand" aria-hidden="true">+</span></summary><div class="case-content">{"".join(contents)}</div></details>')
    evidence = re.search(r'^## 근거 자료\s*(.*?)(?=^# |\Z)', source, re.M | re.S)
    resources = '<div class="resources"><h3>코드와 설계 기록</h3>' + markdown(evidence.group(1)) + '</div>' if evidence else ''
    chips = ''.join('<span>' + inline(value.strip()) + '</span>' for value in tech.split(','))
    cards.append(f'''<a class="project-card {item['accent']}" href="#{item['id']}"><div class="card-top"><span>{item['category']}</span><span>{item['number']}</span></div><h3>{item['name']}</h3><p>{item['description']}</p><div class="card-result"><strong>{item['outcome']}</strong><span>{item['outcome_label']}</span></div><div class="card-bottom"><span>{item['role']}</span><span aria-hidden="true">↗</span></div></a>''')
    projects.append(f'''<section class="project-section {item['accent']}" id="{item['id']}" aria-labelledby="{item['id']}-title"><div class="project-heading"><div class="project-index">{item['number']} / PROJECT</div><h2 id="{item['id']}-title">{item['name']}</h2><p class="project-summary">{item['summary']}</p><div class="project-meta"><span>{item['role']}</span><a href="{item['repository']}" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div><div class="tech">{chips}</div></div><div class="project-body"><div class="architecture"><div class="section-label">SYSTEM ARCHITECTURE</div>{markdown(architecture)}</div><div class="features"><h3>핵심 기능</h3>{markdown(features)}</div><div class="cases"><div class="section-label">{'DEPLOYMENT & OPERATIONS' if item['id'] == 'mylibrary' else 'PROBLEM SOLVING'}</div>{''.join(issue_html)}</div>{resources}</div></section>''')

page = '''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="강현준의 개발 포트폴리오. Jiki 백엔드의 정산 정합성과 성능 개선, 다잡아 프론트엔드의 사용자 경험, 나만의 도서관의 클라우드 배포 기록.">
<meta name="theme-color" content="#f7f7f2"><title>강현준 | 개발 포트폴리오</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body><a class="skip-link" href="#main">본문으로 이동</a><header class="site-header"><a class="brand" href="#top" aria-label="강현준 포트폴리오 처음으로"><span class="brand-mark">H.</span><span>강현준</span></a><nav aria-label="메인 메뉴"><a href="#work">프로젝트</a><a href="#jiki">문제 해결</a><a class="github-link" href="https://github.com/unfl1" target="_blank" rel="noopener noreferrer">GitHub <span aria-hidden="true">↗</span></a></nav></header>
<main id="main"><section class="hero wrap" id="top"><div class="hero-copy"><div class="eyebrow"><span class="dot"></span> DEVELOPER PORTFOLIO</div><h1>개발 과정과<br>문제 해결의 <span>기록.</span></h1><p>백엔드의 정합성부터 사용자 경험, 클라우드 배포까지.<br>직접 구현하고 검증한 세 프로젝트를 정리했습니다.</p><a class="text-link" href="#work">프로젝트 살펴보기 <span aria-hidden="true">↓</span></a></div><div class="hero-note"><div class="note-top"><span>FEATURED / JIKI</span><span class="note-icon" aria-hidden="true">↗</span></div><p class="note-title">반복되는 조회를 줄이고,<br>응답 시간을 단축.</p><div class="note-metric"><span>202</span><span class="metric-arrow" aria-hidden="true">→</span><strong>2</strong></div><div class="note-description">약속 100개 조회 SQL 횟수</div><div class="note-foot"><div><strong>84.8<span>%</span></strong><span>p95 응답 시간 감소</span></div><a href="#jiki" aria-label="Jiki 개선 사례 보기">사례 보기 ↗</a></div><p class="measurement">로컬 k6 · VU 10 · 3회 중앙값 비교</p></div><div class="hero-bottom"><span>BACKEND / FRONTEND / CLOUD</span><span>SELECTED WORK — 03</span></div></section>
<section class="work-section wrap" id="work" aria-labelledby="work-title"><div class="section-heading"><div><div class="eyebrow">SELECTED WORK</div><h2 id="work-title">세 가지 프로젝트.</h2></div><p>기능 구현에서 출발해,<br>각 프로젝트의 문제를 해결한 과정.</p></div><div class="project-grid">__CARDS__</div></section>
<div class="project-nav-shell"><nav class="project-nav wrap" aria-label="프로젝트 바로가기"><span>PROJECTS</span><a href="#jiki">01 Jiki</a><a href="#dajoba">02 다잡아</a><a href="#mylibrary">03 나만의 도서관</a></nav></div><div class="project-list wrap">__PROJECTS__</div>
<section class="closing wrap"><div class="eyebrow">MORE ON GITHUB</div><h2>코드와 기록을 함께.</h2><p>구현 코드와 설계 자료는 각 프로젝트 저장소에서 확인할 수 있습니다.</p><a class="text-link" href="https://github.com/unfl1" target="_blank" rel="noopener noreferrer">GitHub 방문하기 ↗</a></section></main>
<footer class="site-footer wrap"><span>강현준 · 개발 포트폴리오</span><a href="#top">맨 위로 ↑</a></footer>
<dialog id="image-dialog" aria-label="구조도 크게 보기"><div class="dialog-toolbar"><span id="image-caption">구조도</span><button id="close-dialog" type="button" aria-label="이미지 닫기">닫기 <span aria-hidden="true">×</span></button></div><div class="dialog-image"><img id="dialog-img" alt=""></div></dialog></body></html>'''
(ROOT / 'index.html').write_text(page.replace('__CARDS__', ''.join(cards)).replace('__PROJECTS__', ''.join(projects)), encoding='utf-8')
print(f'Built index.html: {len(CONFIG)} projects, {sum(len(re.findall(r"^### ", source, re.M)) for source in sources.values())} cases.')
