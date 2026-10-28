import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('build_digte', Path(__file__).with_name('build_digte.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class PublishingTests(unittest.TestCase):
    def test_formatting_and_whitespace_survive_without_active_html(self):
        source = '  to mellemrum<br><br><blockquote style="color:red"><b>fed</b> og <i>kursiv</i></blockquote><img src=x onerror=alert(1)><script>alert(1)</script>'
        self.assertEqual(builder.sanitize(source), '  to mellemrum<br><br><blockquote><b>fed</b> og <i>kursiv</i></blockquote>')

    def test_hidden_poems_are_removed_and_visible_poems_have_real_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            (root / 'digte/tekster').mkdir(parents=True)
            for name in ['digte.css', 'rediger.html', 'editor.js', 'del.js']:
                (root / 'digte' / name).write_text('')
            (root / 'index.html').write_text('<a href="dr.dk" class="link-108">digte</a>')
            visible = dict(version=1, title='Ord <og> tegn', slug='ord', body='Første<br><br><blockquote><i>    Sidste</i></blockquote>', published=True, homepage=True, order=10)
            hidden = dict(visible, title='HEMMELIG TEKST', slug='skjult', published=False)
            for d in [visible, hidden]:
                (root / 'digte/tekster' / (d['slug'] + '.digt.json')).write_text(json.dumps(d))
            old_root = builder.ROOT
            builder.ROOT = root
            output = Path(tmp) / 'output'
            try:
                builder.build(output)
                page = (output / 'digte/ord/index.html').read_text()
                self.assertIn('Ord &lt;og&gt; tegn', page)
                self.assertIn(visible['body'], page)
                self.assertIn('Del dette digt', page)
                self.assertIn('https://solstorm.org/digte/ord/', page)
                self.assertNotIn('Link til dette digt', page)
                self.assertFalse((output / 'digte/skjult').exists())
                self.assertFalse((output / 'digte/tekster').exists())
                self.assertIn('/digte/ord/', (output / 'sitemap.xml').read_text())
                self.assertNotIn('skjult', (output / 'sitemap.xml').read_text())
                # A missing title must not add the first line as a visible heading.
                visible.pop('title')
                (root / 'digte/tekster/ord.digt.json').write_text(json.dumps(visible))
                builder.build(output)
                page = (output / 'digte/ord/index.html').read_text()
                self.assertIn('<h1 class="sr-only">Digt af Solstorm</h1>', page)
                self.assertNotIn('<h1>Første</h1>', page)
                self.assertIn('<a href="#ord">Første</a>', (output / 'digte/index.html').read_text())
                self.assertNotIn('<h2>', (output / 'digte/index.html').read_text())
                self.assertIn(visible['body'], page)
                visible['published'] = False
                (root / 'digte/tekster/ord.digt.json').write_text(json.dumps(visible))
                builder.build(output)
                self.assertFalse((output / 'digte/ord').exists())
                self.assertEqual(json.loads((output / 'digte/forsidepulje.json').read_text()), [])
            finally:
                builder.ROOT = old_root

    def test_invalid_address_fails_before_publishing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'evil.digt.json'
            path.write_text(json.dumps(dict(version=1, title='Titel', slug='../index', body='tekst', published=True)))
            with self.assertRaisesRegex(ValueError, 'ugyldigt navn'):
                builder.read_poems(Path(tmp))

if __name__ == '__main__':
    unittest.main()
