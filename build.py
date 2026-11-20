#!/usr/bin/env python3
"""Build the static legal pages (GitHub Pages) from the in-app Markdown in ../App/Legal.

Usage:
  python3 build.py --name "Your Name" --email you@example.com \
      --law "the laws of the People's Republic of China" --court "the court with jurisdiction at the developer's location"
Without arguments the 【…】/[…] placeholders are left untouched (and a warning is printed).
"""
import argparse, html, re, pathlib

ROOT = pathlib.Path(__file__).parent
SRC = ROOT.parent / "App" / "Legal"
LANGS = [("en", "English"), ("zh-Hans", "简体中文"), ("zh-Hant", "繁體中文")]
DOCS = {"privacy": "PrivacyPolicy", "terms": "UserAgreement"}
TITLES = {
    "en": {"privacy": "Privacy Policy", "terms": "Terms of Use", "app": "HeartDays"},
    "zh-Hans": {"privacy": "隐私政策", "terms": "用户协议", "app": "心历"},
    "zh-Hant": {"privacy": "隱私政策", "terms": "使用者協議", "app": "心曆"},
}

ap = argparse.ArgumentParser()
ap.add_argument("--name"); ap.add_argument("--email"); ap.add_argument("--law"); ap.add_argument("--court")
a = ap.parse_args()
SUBS = []
if a.name:  SUBS += [("[Developer/Operator Name]", a.name), ("【开发者/运营者名称】", a.name), ("【開發者/營運者名稱】", a.name), ("【開發者/運營者名稱】", a.name)]
if a.email: SUBS += [("[Contact Email]", a.email), ("【联系邮箱】", a.email), ("【聯絡信箱】", a.email), ("【聯繫郵箱】", a.email)]
if a.law:   SUBS += [("[applicable law, e.g., the laws of the People's Republic of China]", a.law)]
if a.law:   SUBS += [("【适用的法律，例如：中华人民共和国法律】", a.law), ("【適用的法律，例如：中華人民共和國法律】", a.law)]
if a.court: SUBS += [("【管辖法院或仲裁机构】", a.court), ("【管轄法院或仲裁機構】", a.court)]
if a.court: SUBS += [("[court or arbitration body with jurisdiction]", a.court)]

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w@])([\w.+-]+@[\w-]+\.[\w.-]+)", r'<a href="mailto:\1">\1</a>', s)
    return s

def md_to_html(text):
    out, in_ul = [], False
    for line in text.splitlines():
        if line.startswith("- "):
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>"); continue
        if in_ul: out.append("</ul>"); in_ul = False
        if line.startswith("# "): out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("## "): out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.strip(): out.append(f"<p>{inline(line)}</p>")
    if in_ul: out.append("</ul>")
    return "\n".join(out)

CSS = """:root{color-scheme:light dark;--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--ac:#0a66d8;--line:#e5e5ea}
@media(prefers-color-scheme:dark){:root{--bg:#000;--fg:#f5f5f7;--mut:#a1a1a6;--ac:#4da3ff;--line:#2c2c2e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.65 -apple-system,BlinkMacSystemFont,"Helvetica Neue","PingFang SC","PingFang TC",sans-serif}
main{max-width:720px;margin:0 auto;padding:24px 16px 64px}nav{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:15px;padding-bottom:12px;border-bottom:1px solid var(--line);margin-bottom:8px}
a{color:var(--ac)}h1{font-size:32px;line-height:1.2;margin:28px 0 8px}h2{font-size:21px;margin:32px 0 4px}p{margin:10px 0}ul{padding-left:22px}li{margin:6px 0}
nav .cur{color:var(--fg);font-weight:600;text-decoration:none}footer{margin-top:48px;color:var(--mut);font-size:14px}"""

def page(title, body, nav):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><main><nav>{nav}</nav>
{body}
</main></body></html>
"""

def fname(doc, lang): return f"{doc}-{lang.lower()}.html"
unresolved = set()
for lang, label in LANGS:
    for doc, stem in DOCS.items():
        text = (SRC / f"{stem}_{lang}.md").read_text(encoding="utf-8")
        for k, v in SUBS: text = text.replace(k, v)
        unresolved |= set(re.findall(r"【[^】]+】|\[(?:Developer|Contact|applicable|court)[^\]]*\]|【[^】]*】", text))
        links = [f'<a href="index.html">{TITLES[lang]["app"]}</a>']
        for d in DOCS:
            cls = ' class="cur"' if d == doc else ""
            links.append(f'<a{cls} href="{fname(d, lang)}">{TITLES[lang][d]}</a>')
        links += [f'<a href="{fname(doc, l)}">{n}</a>' for l, n in LANGS if l != lang]
        (ROOT / fname(doc, lang)).write_text(
            page(f'{TITLES[lang]["app"]} – {TITLES[lang][doc]}', md_to_html(text), " ".join(links)), encoding="utf-8")

rows = "".join(
    f'<p><strong>{n}</strong><br><a href="{fname("privacy", l)}">{TITLES[l]["privacy"]}</a> · <a href="{fname("terms", l)}">{TITLES[l]["terms"]}</a></p>'
    for l, n in LANGS)
(ROOT / "index.html").write_text(page("HeartDays 心历 – Legal", "<h1>HeartDays 心历</h1>\n<p>Privacy Policy and Terms of Use / 隐私政策与用户协议 / 隱私政策與使用者協議</p>\n" + rows, ""), encoding="utf-8")
(ROOT / ".nojekyll").write_text("")
print("Built", len(LANGS) * len(DOCS) + 1, "pages")
if unresolved: print("WARNING: placeholders still present:", *sorted(unresolved), sep="\n  ")
