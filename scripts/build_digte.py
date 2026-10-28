#!/usr/bin/env python3
"""Build static poem pages from editor files, without third-party dependencies."""
import argparse
import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://solstorm.org'
ALLOWED = {'b', 'strong', 'i', 'em', 'br', 'div', 'p', 'blockquote'}
DROP = {'script', 'style', 'iframe', 'object', 'svg', 'math', 'template'}

class SafePoem(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output, self.stack, self.hidden = [], [], 0
    def handle_starttag(self, tag, attrs):
        if tag in DROP:
            self.hidden += 1
        elif not self.hidden and tag in ALLOWED:
            self.output.append('<' + tag + '>')
            if tag != 'br':
                self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != 'br':
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if tag in DROP:
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and tag in self.stack:
            while self.stack:
                current = self.stack.pop()
                self.output.append('</' + current + '>')
                if current == tag:
                    break
    def handle_data(self, data):
        if not self.hidden:
            self.output.append(html.escape(data))
    def result(self):
        return ''.join(self.output) + ''.join('</' + tag + '>' for tag in reversed(self.stack))

def sanitize(text):
    parser = SafePoem()
    parser.feed(text)
    parser.close()
    return parser.result()

def read_poems(folder):
    poems, slugs = [], set()
    for path in sorted(folder.glob('*.digt.json')):
        try:
            if path.stat().st_size > 1024 * 1024:
                raise ValueError('filen er større end 1 MB')
            d = json.loads(path.read_text(encoding='utf-8'))
            if d.get('version') != 1:
                raise ValueError('ukendt filversion')
            for field in ['slug', 'body']:
                if not isinstance(d.get(field), str) or not d[field].strip():
                    raise ValueError('mangler ' + field)
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', d['slug']) or len(d['slug']) > 100:
                raise ValueError('ugyldigt navn i adressen')
            if path.name != d['slug'] + '.digt.json':
                raise ValueError('filnavnet skal være ' + d['slug'] + '.digt.json')
            if d['slug'] in {'tekster', 'assets', 'rediger', 'index'} or d['slug'] in slugs:
                raise ValueError('navnet i adressen er reserveret eller gentaget')
            slugs.add(d['slug'])
            d.setdefault('title', '')
            if not isinstance(d['title'], str) or len(d['title']) > 200 or not isinstance(d.get('note', ''), str) or len(d.get('note', '')) > 500:
                raise ValueError('titlen eller noten er for lang')
            d['title'] = d['title'].strip()
            if type(d.get('order', 10)) is not int or not 0 <= d.get('order', 10) <= 9999:
                raise ValueError('ugyldig rækkefølge')
            if any(type(d.get(field, False)) is not bool for field in ['published', 'homepage']):
                raise ValueError('ugyldigt valg for visning')
            d['body'] = sanitize(d['body'])
            if d.get('published') is True:
                poems.append(d)
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(f'{path.name}: {error}') from error
    return sorted(poems, key=lambda d: (d.get('order', 10), d['title'].casefold()))

def esc(text):
    return html.escape(str(text), quote=True)

def first_line(body):
    plain = re.sub(r'</?(?:br|div|p|blockquote)\b[^>]*>', '\n', body)
    plain = html.unescape(re.sub(r'<[^>]*>', '', plain))
    return next((line.strip()[:100] for line in plain.splitlines() if line.strip()), 'Digt uden titel')

def shell(title, description, url, content, hero='DIGTE.', intro='Et udvalg af Solstorms digte.'):
    heading = f'<h1>{hero}</h1>' if hero else '<h1 class="sr-only">Digt af Solstorm</h1>'
    metadata = json.dumps({'@context': 'https://schema.org', '@type': 'CollectionPage' if url.endswith('/digte/') else 'WebPage', 'name': title, 'url': url, 'inLanguage': 'da', 'about': {'@type': 'Person', '@id': BASE + '/#solstorm', 'name': 'Solstorm'}}, ensure_ascii=False).replace('<', '\\u003c')
    return f'''<!doctype html><html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{esc(url)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{BASE}/biografi/assets/selvportraet.jpg"><link rel="stylesheet" href="/digte/digte.css"><script type="application/ld+json">{metadata}</script></head><body><div class="top"><div class="wrap"><header><a class="brand" href="/">SOLSTORM</a><nav aria-label="Hovedmenu"><a href="/bare-ord/">Bare Ord</a><a href="/biografi/">Biografi</a><a href="/digte/" aria-current="page">Digte</a><a href="mailto:gigasus@gmail.com">Kontakt</a></nav></header><p class="eyebrow">Solstorm / Poesi</p>{heading}<p class="intro">{intro}</p></div></div><main class="wrap">{content}</main><footer><div class="wrap">Solstorm / Poesi · <a href="/biografi/">Om digteren ↗</a></div></footer><script src="/digte/del.js" defer></script></body></html>'''

def share_button(d, address):
    label = d['title'] or first_line(d['body'])
    share_title = label + ' - Solstorm'
    icon = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m9 10.5 6-4M9 13.5l6 4"/></svg>'
    return f'<button type="button" class="share-trigger" data-share-poem="{BASE}{address}" data-share-title="{esc(share_title)}" data-share-label="{esc(label)}" aria-haspopup="dialog">{icon}Del dette digt</button>'

def note(d):
    return '<p class="poem-note">' + esc(d['note']) + '</p>' if d.get('note') else ''

def build(output):
    output = Path(output).resolve()
    if output == ROOT or ROOT.is_relative_to(output) or output in [ROOT / 'digte', ROOT / 'biografi', ROOT / 'bare-ord']:
        raise ValueError('vælg en separat mappe til den byggede side')
    poems = read_poems(ROOT / 'digte' / 'tekster')
    output.mkdir(parents=True, exist_ok=True)
    for name in ['index.html', 'robots.txt', 'sitemap.xml', 'CNAME']:
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, output / name)
    for name in ['images', 'biografi', 'bare-ord']:
        if (ROOT / name).exists():
            shutil.copytree(ROOT / name, output / name, dirs_exist_ok=True)
    target = output / 'digte'
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    for name in ['digte.css', 'rediger.html', 'editor.js', 'del.js']:
        shutil.copy2(ROOT / 'digte' / name, target / name)
    nav, articles, pool = [], [], []
    for d in poems:
        slug, title = d['slug'], esc(d['title'])
        label = esc(d['title'] or first_line(d['body']))
        address = '/digte/' + slug + '/'
        nav.append(f'<a href="#{slug}">{label}</a>')
        poem_heading = f'<h2><a href="{address}">{title}</a></h2>' if d['title'] else ''
        articles.append(f'<article class="poem-card" id="{slug}">{poem_heading}<div class="poem-text">{d["body"]}</div>{note(d)}{share_button(d, address)}</article>')
        page = f'<article class="single"><a class="back" href="/digte/">← Alle digte</a><div class="poem-text">{d["body"]}</div>{note(d)}{share_button(d, address)}</article>'
        folder = target / slug
        folder.mkdir()
        page_title = (d['title'] or first_line(d['body'])) + ' - Solstorm'
        description = 'Læs digtet ' + d['title'] + ' af Solstorm.' if d['title'] else 'Læs et digt uden titel af Solstorm.'
        (folder / 'index.html').write_text(shell(page_title, description, BASE + address, page, hero=title, intro='Et digt af Solstorm.'), encoding='utf-8')
        if d.get('homepage') is True:
            pool.append({'title': d['title'], 'url': address, 'body': d['body']})
    collection = '<div class="index-layout"><nav class="poem-list" aria-label="Vælg et digt">' + ''.join(nav) + '</nav><div>' + ''.join(articles) + '</div></div>' if poems else '<p class="empty">Digtene er på vej.</p>'
    (target / 'index.html').write_text(shell('Digte af Solstorm', 'Læs et udvalg af Solstorms digte.', BASE + '/digte/', collection), encoding='utf-8')
    # Prepared for a future homepage rotation; no script is added to the homepage.
    (target / 'forsidepulje.json').write_text(json.dumps(pool, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    homepage = output / 'index.html'
    if homepage.exists():
        homepage.write_text(homepage.read_text().replace('href="dr.dk" class="link-108">digte', 'href="/digte/" class="link-108">digte'), encoding='utf-8')
    sitemap = output / 'sitemap.xml'
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    tree = ET.parse(sitemap) if sitemap.exists() else ET.ElementTree(ET.Element('{' + ns + '}urlset'))
    root = tree.getroot()
    for url in list(root):
        loc = url.find('{' + ns + '}loc')
        if loc is not None and (loc.text or '').startswith(BASE + '/digte/'):
            root.remove(url)
    for url in [BASE + '/digte/'] + [BASE + '/digte/' + d['slug'] + '/' for d in poems]:
        item = ET.SubElement(root, '{' + ns + '}url')
        ET.SubElement(item, '{' + ns + '}loc').text = url
    tree.write(sitemap, encoding='utf-8', xml_declaration=True)
    print(f'Bygget {len(poems)} digte i {output}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT / '_site'))
    args = parser.parse_args()
    try:
        build(args.output)
    except ValueError as error:
        parser.exit(1, 'Fejl: ' + str(error) + '\n')
