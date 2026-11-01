from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import re
import json
import datetime
import html as html_lib

load_dotenv()

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_URL     = 'https://api.groq.com/openai/v1/chat/completions'
AI_MODEL     = 'openai/gpt-oss-120b'
SAVES_FILE   = 'saved_portfolios.json'

# ─────────────────────────────────────────────
# Themes, fonts, allowed settings
# ─────────────────────────────────────────────
THEMES = {
    'dark':     {'bg': '#0a0a0f', 'bg2': '#111118', 'bg3': '#16161f', 'primary': '#e94560', 'text': '#ffffff', 'text2': '#888899', 'border': '#1e1e2e'},
    'blue':     {'bg': '#0a0f1a', 'bg2': '#0f1825', 'bg3': '#142030', 'primary': '#4f8ef7', 'text': '#ffffff', 'text2': '#6a8fb0', 'border': '#1a2535'},
    'purple':   {'bg': '#0d0a1a', 'bg2': '#130f25', 'bg3': '#1a1530', 'primary': '#8b5cf6', 'text': '#ffffff', 'text2': '#8878b0', 'border': '#1e1835'},
    'minimal':  {'bg': '#ffffff', 'bg2': '#f8f9fa', 'bg3': '#f0f2f5', 'primary': '#2563eb', 'text': '#111827', 'text2': '#6b7280', 'border': '#e5e7eb'},
    'green':    {'bg': '#0a0f0a', 'bg2': '#0f1a0f', 'bg3': '#142014', 'primary': '#22c55e', 'text': '#ffffff', 'text2': '#6a9070', 'border': '#1a2e1a'},
    'orange':   {'bg': '#0f0a05', 'bg2': '#1a1005', 'bg3': '#201508', 'primary': '#f97316', 'text': '#ffffff', 'text2': '#a08060', 'border': '#2e1e05'},
    'pink':     {'bg': '#0f0a0f', 'bg2': '#1a0f1a', 'bg3': '#201520', 'primary': '#ec4899', 'text': '#ffffff', 'text2': '#a070a0', 'border': '#2e1535'},
    'teal':     {'bg': '#0a0f0f', 'bg2': '#0f1a1a', 'bg3': '#142020', 'primary': '#14b8a6', 'text': '#ffffff', 'text2': '#60a0a0', 'border': '#1a2e2e'},
    'yellow':   {'bg': '#0f0f05', 'bg2': '#1a1a0a', 'bg3': '#202010', 'primary': '#eab308', 'text': '#ffffff', 'text2': '#a0a060', 'border': '#2e2e10'},
    'midnight': {'bg': '#05050f', 'bg2': '#0a0a1a', 'bg3': '#0f0f25', 'primary': '#6366f1', 'text': '#e0e0ff', 'text2': '#7070a0', 'border': '#15153a'},
    'rose':     {'bg': '#0f0505', 'bg2': '#1a0a0a', 'bg3': '#200f0f', 'primary': '#f43f5e', 'text': '#ffffff', 'text2': '#a06070', 'border': '#2e1520'},
    'cyan':     {'bg': '#050f0f', 'bg2': '#0a1a1a', 'bg3': '#0f2020', 'primary': '#06b6d4', 'text': '#ffffff', 'text2': '#60a0b0', 'border': '#102e35'},
}

FONTS = {
    'modern':  ('Inter',            'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap'),
    'elegant': ('Playfair Display', 'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&display=swap'),
    'tech':    ('JetBrains Mono',   'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap'),
    'playful': ('Poppins',          'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap'),
}

SECTIONS    = ['about', 'skills', 'projects', 'contact']
TEXT_LIMITS = {'tagline': 160, 'bio': 600, 'title': 80, 'name': 60}


# ─────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────
def esc(value):
    return html_lib.escape(str(value or ''), quote=True)


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_string(hex_color):
    return ', '.join(str(n) for n in hex_to_rgb(hex_color))


def on_color(hex_color):
    """Pick dark or white text so it stays readable on top of a color."""
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#111111' if luminance > 0.6 else '#ffffff'


def safe_url(url, fallback='#'):
    url = (url or '').strip()
    if not url:
        return fallback
    if re.match(r'^(https?://|mailto:|#)', url, re.IGNORECASE):
        return url
    return 'https://' + url


def html_to_text(page_html):
    text = re.sub(r'(?is)<(script|style).*?</\1>', ' ', page_html or '')
    text = re.sub(r'(?s)<[^>]+>', ' ', text)
    return html_lib.unescape(re.sub(r'\s+', ' ', text)).strip()


def render(template, mapping):
    """Replace %%TOKEN%% in one pass (values are never re-scanned)."""
    return re.sub(r'%%(\w+)%%', lambda m: str(mapping.get(m.group(1), m.group(0))), template)


def extract_json(text):
    text = re.sub(r'```(?:json)?', '', text or '').strip()
    start = text.find('{')
    end   = text.rfind('}') + 1
    if start == -1 or end <= start:
        raise ValueError('The AI did not return JSON')
    return json.loads(text[start:end])


def call_groq(prompt, max_tokens=600, temperature=0.5, timeout=45):
    if not GROQ_API_KEY:
        raise RuntimeError('GROQ_API_KEY not configured')

    headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        'model':            AI_MODEL,
        'messages':         [{'role': 'user', 'content': prompt}],
        'max_tokens':       max_tokens,
        'temperature':      temperature,
        'reasoning_effort': 'low',
    }

    result = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout).json()

    # If this model rejects reasoning_effort, retry without it
    if 'choices' not in result and 'reasoning_effort' in json.dumps(result).lower():
        payload.pop('reasoning_effort')
        result = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout).json()

    if 'choices' not in result:
        raise RuntimeError(result.get('error', {}).get('message', 'Unknown AI error'))

    return (result['choices'][0]['message'].get('content') or '').strip()


# ─────────────────────────────────────────────
# Edit settings (the safe way to edit)
# ─────────────────────────────────────────────
def clean_overrides(raw):
    """Keep only known, safe settings. A value of None means 'remove this setting'."""
    clean = {}
    if not isinstance(raw, dict):
        return clean

    if raw.get('theme') in THEMES:
        clean['theme'] = raw['theme']
    if raw.get('font_style') in FONTS:
        clean['font_style'] = raw['font_style']

    color = raw.get('primary_color')
    if isinstance(color, str):
        color = color.strip()
        if color.lower() == 'default':
            clean['primary_color'] = None
        elif re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            clean['primary_color'] = color

    if 'font_scale' in raw:
        try:
            clean['font_scale'] = round(min(max(float(raw['font_scale']), 0.9), 1.4), 2)
        except (TypeError, ValueError):
            pass

    if raw.get('hero_size') in ('small', 'normal', 'large'):
        clean['hero_size'] = raw['hero_size']
    if raw.get('animations') in ('none', 'normal', 'more'):
        clean['animations'] = raw['animations']
    if isinstance(raw.get('dark_toggle'), bool):
        clean['dark_toggle'] = raw['dark_toggle']

    for key in ('hide_sections', 'show_sections'):
        if isinstance(raw.get(key), list):
            clean[key] = list(dict.fromkeys(s for s in raw[key] if s in SECTIONS))

    for key, limit in TEXT_LIMITS.items():
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            clean[key] = value.strip()[:limit]

    return clean


def merge_overrides(current, changes):
    merged  = dict(current)
    changes = dict(changes)

    to_hide = changes.pop('hide_sections', [])
    to_show = changes.pop('show_sections', [])
    if to_hide or to_show:
        hidden = (set(merged.get('hide_sections', [])) | set(to_hide)) - set(to_show)
        merged['hide_sections'] = [s for s in SECTIONS if s in hidden]

    # Picking a new theme resets a custom color, unless a color was also requested
    if 'theme' in changes and 'primary_color' not in changes:
        merged.pop('primary_color', None)

    for key, value in changes.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value

    return merged


EDIT_PROMPT = """You change a portfolio website by choosing settings. Turn the user's request into JSON.

Settings you may change (use only these keys):
- "primary_color": a hex color like "#d4af37", or "default" to go back to the theme color
- "theme": one of dark, blue, purple, minimal, green, orange, pink, teal, yellow, midnight, rose, cyan
- "font_style": one of modern, elegant, tech, playful
- "font_scale": a number from 0.9 to 1.4 (1.0 is normal size)
- "hero_size": small, normal or large
- "animations": none, normal or more
- "dark_toggle": true or false (adds a light/dark switch button)
- "hide_sections": list of sections to hide, from: about, skills, projects, contact
- "show_sections": list of sections to show again, from: about, skills, projects, contact
- "tagline", "bio", "title", "name": new text

Current settings: __CURRENT__
User request: __REQUEST__

Reply with ONLY JSON in this shape:
{"changes": {"only the keys that must change": "value"}, "summary": "one short sentence"}

If the request needs something that is not in the list (for example adding a brand new section), reply:
{"changes": {}, "unsupported": "one short sentence explaining what is not possible"}"""


# ─────────────────────────────────────────────
# Saves
# ─────────────────────────────────────────────
def load_saves():
    if os.path.exists(SAVES_FILE):
        try:
            with open(SAVES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return []


def write_saves(saves):
    with open(SAVES_FILE, 'w', encoding='utf-8') as f:
        json.dump(saves, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Page templates (CSS and JS use %%TOKENS%%)
# ─────────────────────────────────────────────
CSS_TEMPLATE = r"""
:root {
  --bg: %%BG%%;
  --bg2: %%BG2%%;
  --bg3: %%BG3%%;
  --primary: %%PRIMARY%%;
  --on-primary: %%ON_PRIMARY%%;
  --text: %%TEXT%%;
  --text2: %%TEXT2%%;
  --border: %%BORDER%%;
  --nav-bg: %%NAV_BG%%;
}

html.flip {
  --bg: %%ALT_BG%%;
  --bg2: %%ALT_BG2%%;
  --bg3: %%ALT_BG3%%;
  --text: %%ALT_TEXT%%;
  --text2: %%ALT_TEXT2%%;
  --border: %%ALT_BORDER%%;
  --nav-bg: %%ALT_NAV_BG%%;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html { scroll-behavior: smooth; font-size: %%FONT_SIZE%%; }

body {
  font-family: '%%FONT_NAME%%', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
  transition: background 0.3s, color 0.3s;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }

/* Navigation */
nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  padding: 16px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--nav-bg);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.nav-logo { font-size: 1.2rem; font-weight: 800; color: var(--primary); text-decoration: none; }
.nav-links { display: flex; gap: 32px; list-style: none; align-items: center; }
.nav-links a { color: var(--text2); text-decoration: none; font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }
.nav-links a:hover { color: var(--primary); }
.nav-links a.nav-cta { padding: 8px 20px; border-radius: 50px; background: var(--primary); color: var(--on-primary); font-weight: 600; font-size: 0.85rem; }
.nav-links a.nav-cta:hover { color: var(--on-primary); opacity: 0.9; }

.nav-right { display: flex; align-items: center; gap: 12px; }

.flip-btn {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}
.flip-btn:hover { border-color: var(--primary); }

.hamburger { display: none; flex-direction: column; gap: 5px; cursor: pointer; background: none; border: none; padding: 4px; }
.hamburger span { width: 24px; height: 2px; background: var(--text); border-radius: 2px; }

.mobile-menu {
  display: none;
  position: fixed;
  top: 65px; left: 0; right: 0;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  padding: 20px;
  z-index: 99;
  flex-direction: column;
  gap: 16px;
}
.mobile-menu a { color: var(--text); text-decoration: none; font-size: 1rem; font-weight: 500; }
.mobile-menu.open { display: flex; }

/* Hero */
#hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 120px 40px 80px;
  position: relative;
  overflow: hidden;
  max-width: none;
  margin: 0;
}

#hero-canvas { position: absolute; inset: 0; z-index: 0; }

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 60px;
}

.hero-text { flex: 1; }

.hero-greeting {
  font-size: 1rem;
  color: var(--primary);
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 16px;
}

.hero-name {
  font-size: %%HERO_NAME_SIZE%%;
  font-weight: 900;
  line-height: 1.1;
  margin-bottom: 16px;
  background: linear-gradient(135deg, var(--text), var(--primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-title { font-size: clamp(1.2rem, 3vw, 1.8rem); color: var(--text2); margin-bottom: 20px; font-weight: 400; }

.hero-title span {
  color: var(--primary);
  font-weight: 700;
  border-right: 2px solid var(--primary);
  padding-right: 4px;
  animation: blink 1s infinite;
}

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.hero-tagline { font-size: 1rem; color: var(--text2); margin-bottom: 32px; max-width: 500px; line-height: 1.7; }

.hero-btns { display: flex; gap: 14px; flex-wrap: wrap; }

.btn-primary {
  padding: 14px 32px;
  border-radius: 50px;
  background: var(--primary);
  color: var(--on-primary);
  font-size: 0.95rem;
  font-weight: 700;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3);
}
.btn-primary:hover { transform: translateY(-3px); opacity: 0.9; }

.btn-secondary {
  padding: 14px 32px;
  border-radius: 50px;
  border: 2px solid var(--border);
  color: var(--text);
  font-size: 0.95rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s;
}
.btn-secondary:hover { border-color: var(--primary); color: var(--primary); }

.hero-social { display: flex; gap: 12px; margin-top: 28px; }

.social-link {
  width: 42px; height: 42px;
  border-radius: 50%;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text2);
  text-decoration: none;
  font-size: 1rem;
  transition: all 0.2s;
}
.social-link:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-2px); }

.hero-photo-wrap { flex-shrink: 0; }

.hero-photo {
  width: 280px; height: 280px;
  border-radius: 30px;
  object-fit: cover;
  border: 3px solid var(--primary);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}

.hero-avatar {
  width: 280px; height: 280px;
  border-radius: 30px;
  background: linear-gradient(135deg, var(--primary), var(--bg3));
  border: 3px solid var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 5rem;
  font-weight: 900;
  color: var(--on-primary);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

/* Sections */
section { padding: 100px 40px; max-width: 1100px; margin: 0 auto; }

.section-tag {
  display: inline-block;
  padding: 5px 14px;
  border-radius: 20px;
  background: rgba(%%PRIMARY_RGB%%, 0.12);
  border: 1px solid var(--border);
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 14px;
}

.section-title { font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 900; margin-bottom: 12px; line-height: 1.2; }
.section-title span { color: var(--primary); }
.section-sub { color: var(--text2); font-size: 1rem; max-width: 600px; line-height: 1.7; margin-bottom: 48px; }

/* About */
.about-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center; }
.about-text p { color: var(--text2); font-size: 1rem; line-height: 1.8; margin-bottom: 20px; }
.about-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 32px; }
.about-stat { text-align: center; padding: 20px; background: var(--bg2); border: 1px solid var(--border); border-radius: 16px; }
.about-stat-num { font-size: 2rem; font-weight: 900; color: var(--primary); }
.about-stat-label { font-size: 0.75rem; color: var(--text2); margin-top: 4px; }
.about-photo { width: 100%; border-radius: 20px; object-fit: cover; border: 2px solid var(--border); }
.about-avatar {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--primary), var(--bg3));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
  color: var(--on-primary);
  border: 2px solid var(--border);
}

/* Skills (honest tags, no made-up percentages) */
.skills-wrap { display: flex; flex-wrap: wrap; gap: 12px; }

.skill-chip {
  padding: 10px 22px;
  border-radius: 50px;
  background: var(--bg2);
  border: 1px solid var(--border);
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
}
.skill-chip:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-3px); }

/* Projects */
.projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; }

.project-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 28px;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.project-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary), transparent);
  transform: scaleX(0);
  transition: transform 0.3s;
}

.project-card:hover { transform: translateY(-6px); border-color: var(--primary); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); }
.project-card:hover::before { transform: scaleX(1); }

.project-card-top { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.project-icon { font-size: 1.5rem; }
.project-name { font-size: 1.05rem; font-weight: 700; }
.project-desc { color: var(--text2); font-size: 0.88rem; line-height: 1.6; margin-bottom: 16px; }
.project-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }

.tech-tag {
  padding: 3px 10px;
  border-radius: 20px;
  background: var(--bg3);
  border: 1px solid var(--border);
  font-size: 0.72rem;
  color: var(--primary);
}

.project-link {
  color: var(--primary);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: gap 0.2s;
}
.project-link:hover { gap: 8px; }

/* Contact */
.contact-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: start; }
.contact-wrap.no-form { grid-template-columns: 1fr; max-width: 560px; }
.contact-info p { color: var(--text2); font-size: 1rem; line-height: 1.7; margin-bottom: 28px; }
.contact-items { display: flex; flex-direction: column; gap: 14px; }

.contact-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 12px;
  text-decoration: none;
  color: var(--text);
  transition: all 0.2s;
}
.contact-item:hover { border-color: var(--primary); color: var(--primary); transform: translateX(4px); }
.contact-item i { width: 18px; color: var(--primary); }
.contact-item span { font-size: 0.88rem; }

.contact-form-wrap { background: var(--bg2); border: 1px solid var(--border); border-radius: 20px; padding: 32px; }
.cf-group { margin-bottom: 18px; }
.cf-group label { display: block; font-size: 0.78rem; color: var(--text2); font-weight: 600; margin-bottom: 6px; }

.cf-group input,
.cf-group textarea {
  width: 100%;
  padding: 11px 14px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg3);
  color: var(--text);
  font-size: 0.9rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.cf-group input:focus,
.cf-group textarea:focus { border-color: var(--primary); }
.cf-group textarea { min-height: 110px; resize: vertical; }

.cf-btn {
  width: 100%;
  padding: 13px;
  border-radius: 10px;
  border: none;
  background: var(--primary);
  color: var(--on-primary);
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.cf-btn:hover { opacity: 0.9; transform: translateY(-1px); }

/* Footer + scroll to top */
footer { border-top: 1px solid var(--border); padding: 40px; text-align: center; color: var(--text2); font-size: 0.85rem; }
footer span { color: var(--primary); }

#scroll-top {
  position: fixed;
  bottom: 24px; right: 24px;
  width: 44px; height: 44px;
  border-radius: 50%;
  background: var(--primary);
  border: none;
  color: var(--on-primary);
  font-size: 1rem;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 50;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s;
}
#scroll-top.show { display: flex; }
#scroll-top:hover { transform: translateY(-3px); }

/* Fade in */
.fade-in { opacity: 0; transform: translateY(24px); transition: all 0.6s ease; }
.fade-in.visible { opacity: 1; transform: translateY(0); }

/* Responsive */
@media (max-width: 768px) {
  nav { padding: 14px 20px; }
  .nav-links { display: none; }
  .hamburger { display: flex; }
  #hero { padding: 100px 20px 60px; }
  .hero-content { flex-direction: column-reverse; gap: 30px; }
  .hero-photo, .hero-avatar { width: 180px; height: 180px; font-size: 3rem; }
  section { padding: 60px 20px; }
  .about-grid, .contact-wrap { grid-template-columns: 1fr; }
  .about-stats { grid-template-columns: 1fr 1fr; }
}

%%EXTRA_CSS%%
"""

JS_TEMPLATE = r"""
const TITLES         = %%TITLES_JSON%%
const PARTICLE_COUNT = %%PARTICLE_COUNT%%
const PRIMARY_RGB    = '%%PRIMARY_RGB%%'
const CONTACT_EMAIL  = %%EMAIL_JSON%%

// Typewriter
let titleIndex = 0
let charIndex  = 0
let deleting   = false
const typewriterEl = document.getElementById('typewriter')

function typewrite() {
  const current = TITLES[titleIndex]
  if (!deleting) {
    charIndex++
    typewriterEl.textContent = current.substring(0, charIndex)
    if (charIndex === current.length) {
      deleting = true
      setTimeout(typewrite, 1800)
      return
    }
  } else {
    charIndex--
    typewriterEl.textContent = current.substring(0, charIndex)
    if (charIndex === 0) {
      deleting = false
      titleIndex = (titleIndex + 1) % TITLES.length
    }
  }
  setTimeout(typewrite, deleting ? 50 : 90)
}

typewrite()

// Hero particles
const canvas    = document.getElementById('hero-canvas')
const ctx       = canvas.getContext('2d')
const particles = []

function resizeCanvas() {
  canvas.width  = canvas.parentElement.offsetWidth
  canvas.height = canvas.parentElement.offsetHeight
}

resizeCanvas()
window.addEventListener('resize', resizeCanvas)

for (let i = 0; i < PARTICLE_COUNT; i++) {
  particles.push({
    x:       Math.random() * canvas.width,
    y:       Math.random() * canvas.height,
    size:    Math.random() * 2 + 0.5,
    speedX:  (Math.random() - 0.5) * 0.4,
    speedY:  (Math.random() - 0.5) * 0.4,
    opacity: Math.random() * 0.4 + 0.1,
  })
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  particles.forEach(p => {
    p.x += p.speedX
    p.y += p.speedY
    if (p.x < 0 || p.x > canvas.width)  p.speedX *= -1
    if (p.y < 0 || p.y > canvas.height) p.speedY *= -1
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${PRIMARY_RGB}, ${p.opacity})`
    ctx.fill()
  })

  particles.forEach((p1, i) => {
    particles.slice(i + 1).forEach(p2 => {
      const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y)
      if (dist < 120) {
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = `rgba(${PRIMARY_RGB}, ${0.06 * (1 - dist / 120)})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    })
  })

  requestAnimationFrame(animateParticles)
}

if (PARTICLE_COUNT > 0) animateParticles()

// Fade in on scroll
const fadeObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('visible')
  })
}, { threshold: 0.1 })

document.querySelectorAll('.fade-in').forEach(el => fadeObserver.observe(el))

// Scroll to top
window.addEventListener('scroll', () => {
  document.getElementById('scroll-top').classList.toggle('show', window.scrollY > 400)
})

function scrollTopNow() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Mobile menu
function toggleMenu() {
  document.getElementById('mobile-menu').classList.toggle('open')
}

// Smooth scroll for in-page links
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', event => {
    const target = link.getAttribute('href')
    if (target.length < 2) return
    const el = document.querySelector(target)
    if (!el) return
    event.preventDefault()
    el.scrollIntoView({ behavior: 'smooth' })
    document.getElementById('mobile-menu').classList.remove('open')
  })
})

// Light / dark switch
const flipButton = document.getElementById('theme-flip')
if (flipButton) {
  flipButton.addEventListener('click', () => {
    document.documentElement.classList.toggle('flip')
  })
}

// Contact form opens the visitor's email app
function sendMail() {
  if (!CONTACT_EMAIL) return
  const name    = document.getElementById('cf-name').value.trim()
  const email   = document.getElementById('cf-email').value.trim()
  const message = document.getElementById('cf-message').value.trim()
  const subject = encodeURIComponent('Portfolio message from ' + (name || 'a visitor'))
  const body    = encodeURIComponent(message + '\n\n- ' + name + (email ? ' (' + email + ')' : ''))
  window.location.href = 'mailto:' + CONTACT_EMAIL + '?subject=' + subject + '&body=' + body
}
"""


# ─────────────────────────────────────────────
# Build the portfolio page
# ─────────────────────────────────────────────
def build_portfolio_html(form, overrides=None):
    ov = overrides or {}

    # Content (edit settings win over the original form)
    name     = ov.get('name')  or form.get('name', '')
    title    = ov.get('title') or form.get('title', '')
    bio      = ov.get('bio')   or form.get('bio', '')
    tagline  = ov.get('tagline') or 'I build things that make a difference.'
    projects = [p for p in (form.get('projects') or []) if p.get('name')]
    email    = (form.get('email') or '').strip()
    github   = (form.get('github') or '').strip().lstrip('@')
    linkedin = (form.get('linkedin') or '').strip()
    photo    = form.get('photo') or ''

    skills_list = [s.strip() for s in (form.get('skills') or '').split(',') if s.strip()]

    # Look and feel
    theme = ov.get('theme') or form.get('theme') or 'dark'
    if theme not in THEMES:
        theme = 'dark'

    font_key = ov.get('font_style') or form.get('font_style') or 'modern'
    if font_key not in FONTS:
        font_key = 'modern'
    font_name, font_url = FONTS[font_key]

    colors = dict(THEMES[theme])
    if ov.get('primary_color'):
        colors['primary'] = ov['primary_color']

    alt = THEMES['dark'] if theme == 'minimal' else THEMES['minimal']

    font_scale  = float(ov.get('font_scale', 1.0))
    hero_size   = ov.get('hero_size', 'normal')
    animations  = ov.get('animations', 'normal')
    dark_toggle = bool(ov.get('dark_toggle', False))

    hero_sizes = {
        'small':  'clamp(2rem, 4.5vw, 3.2rem)',
        'normal': 'clamp(2.5rem, 6vw, 4.5rem)',
        'large':  'clamp(3.2rem, 9vw, 6.5rem)',
    }
    particle_counts = {'none': 0, 'normal': 60, 'more': 120}

    extra_css = ''
    if animations == 'none':
        extra_css = """
#hero-canvas { display: none; }
html { scroll-behavior: auto; }
.fade-in { opacity: 1 !important; transform: none !important; transition: none !important; }
"""
    elif animations == 'more':
        extra_css = """
.hero-photo, .hero-avatar { animation: float 4s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
.skill-chip, .about-stat { transition: transform 0.3s, border-color 0.3s; }
.about-stat:hover { transform: translateY(-4px); border-color: var(--primary); }
.social-link, .contact-item { transition: all 0.3s; }
"""

    # Sections that are hidden (by the user, or because there is nothing to show)
    hide = set(ov.get('hide_sections', []))
    if not skills_list:
        hide.add('skills')
    if not projects:
        hide.add('projects')

    # Small text pieces
    name_first = (name.split() or ['Portfolio'])[0]
    initials   = ''.join(w[0].upper() for w in name.split()[:2]) or 'ME'

    if photo:
        hero_photo  = f'<img src="data:image/jpeg;base64,{photo}" alt="{esc(name)}" class="hero-photo" />'
        about_photo = f'<img src="data:image/jpeg;base64,{photo}" alt="{esc(name)}" class="about-photo" />'
    else:
        hero_photo  = f'<div class="hero-avatar">{esc(initials)}</div>'
        about_photo = f'<div class="about-avatar">{esc(initials)}</div>'

    github_url   = safe_url(github if github.startswith('http') else f'https://github.com/{github}') if github else ''
    linkedin_url = safe_url(linkedin) if linkedin else ''

    social = ''
    if email:
        social += f'<a href="mailto:{esc(email)}" class="social-link" aria-label="Email"><i class="fas fa-envelope"></i></a>'
    if github_url:
        social += f'<a href="{esc(github_url)}" target="_blank" class="social-link" aria-label="GitHub"><i class="fab fa-github"></i></a>'
    if linkedin_url:
        social += f'<a href="{esc(linkedin_url)}" target="_blank" class="social-link" aria-label="LinkedIn"><i class="fab fa-linkedin"></i></a>'

    contact_links = ''
    if email:
        contact_links += f'<a href="mailto:{esc(email)}" class="contact-item"><i class="fas fa-envelope"></i><span>{esc(email)}</span></a>'
    if github_url:
        contact_links += f'<a href="{esc(github_url)}" target="_blank" class="contact-item"><i class="fab fa-github"></i><span>{esc(github_url.replace("https://", ""))}</span></a>'
    if linkedin_url:
        contact_links += f'<a href="{esc(linkedin_url)}" target="_blank" class="contact-item"><i class="fab fa-linkedin"></i><span>LinkedIn</span></a>'

    # Navigation
    nav_items = [('about', 'About'), ('skills', 'Skills'), ('projects', 'Projects')]
    nav_links    = ''.join(f'<li><a href="#{k}">{label}</a></li>' for k, label in nav_items if k not in hide)
    mobile_links = ''.join(f'<a href="#{k}">{label}</a>' for k, label in nav_items if k not in hide)
    if 'contact' not in hide:
        nav_links    += '<li><a href="#contact" class="nav-cta">Contact</a></li>'
        mobile_links += '<a href="#contact">Contact</a>'

    hero_btns = ''
    if 'projects' not in hide:
        hero_btns += '<a href="#projects" class="btn-primary">🚀 View My Work</a>'
    if 'contact' not in hide:
        hero_btns += '<a href="#contact" class="btn-secondary">📬 Get In Touch</a>'

    flip_button = '<button class="flip-btn" id="theme-flip" aria-label="Switch light or dark mode">🌓</button>' if dark_toggle else ''

    # About
    about_section = ''
    if 'about' not in hide:
        bio_html = esc(bio) if bio else f"Hi! I'm {esc(name)}, a passionate {esc(title)} who loves building things that make a difference. I enjoy solving complex problems and creating elegant solutions."
        about_section = f'''
  <section id="about">
    <div class="fade-in">
      <div class="section-tag">About Me</div>
      <h2 class="section-title">Who am <span>I?</span></h2>
      <p class="section-sub">A little bit about me and what I do</p>
    </div>
    <div class="about-grid fade-in">
      <div class="about-text">
        <p>{bio_html}</p>
        <p>I'm always looking for new challenges and opportunities to grow. Whether it's a side project or a professional endeavor, I bring my best to everything I do.</p>
        <div class="about-stats">
          <div class="about-stat"><div class="about-stat-num">{len(projects)}</div><div class="about-stat-label">Projects</div></div>
          <div class="about-stat"><div class="about-stat-num">{len(skills_list)}</div><div class="about-stat-label">Skills</div></div>
          <div class="about-stat"><div class="about-stat-num">100%</div><div class="about-stat-label">Passion</div></div>
        </div>
      </div>
      <div class="about-img-wrap">{about_photo}</div>
    </div>
  </section>
'''

    # Skills (only what the person actually entered)
    skills_section = ''
    if 'skills' not in hide:
        chips = ''.join(f'<span class="skill-chip">{esc(skill)}</span>' for skill in skills_list[:24])
        skills_section = f'''
  <section id="skills">
    <div class="fade-in">
      <div class="section-tag">Skills</div>
      <h2 class="section-title">What I <span>Work With</span></h2>
      <p class="section-sub">Technologies and tools I use to bring ideas to life</p>
    </div>
    <div class="skills-wrap fade-in">{chips}</div>
  </section>
'''

    # Projects
    projects_section = ''
    if 'projects' not in hide:
        cards = ''
        for p in projects:
            tags = ''.join(f'<span class="tech-tag">{esc(t.strip())}</span>' for t in (p.get('tech') or '').split(',') if t.strip())
            cards += f'''
      <div class="project-card">
        <div class="project-card-top"><div class="project-icon">🚀</div><h3 class="project-name">{esc(p.get('name'))}</h3></div>
        <p class="project-desc">{esc(p.get('desc'))}</p>
        <div class="project-tags">{tags}</div>
        <a href="{esc(safe_url(p.get('url')))}" target="_blank" class="project-link">View Project →</a>
      </div>'''
        projects_section = f'''
  <section id="projects">
    <div class="fade-in">
      <div class="section-tag">Portfolio</div>
      <h2 class="section-title">My <span>Projects</span></h2>
      <p class="section-sub">Things I've built that I'm proud of</p>
    </div>
    <div class="projects-grid fade-in">{cards}
    </div>
  </section>
'''

    # Contact
    contact_section = ''
    if 'contact' not in hide:
        contact_form = ''
        if email:
            contact_form = f'''
      <div class="contact-form-wrap">
        <div class="cf-group"><label>Your Name</label><input type="text" id="cf-name" placeholder="Your name" /></div>
        <div class="cf-group"><label>Your Email</label><input type="email" id="cf-email" placeholder="you@example.com" /></div>
        <div class="cf-group"><label>Message</label><textarea id="cf-message" placeholder="Hi {esc(name_first)}, I'd love to..."></textarea></div>
        <button class="cf-btn" onclick="sendMail()">Send via Email ✉️</button>
      </div>'''
        wrap_class = 'contact-wrap fade-in' + ('' if email else ' no-form')
        contact_section = f'''
  <section id="contact">
    <div class="fade-in">
      <div class="section-tag">Contact</div>
      <h2 class="section-title">Let's <span>Work Together</span></h2>
      <p class="section-sub">Have a project in mind? I'd love to hear from you!</p>
    </div>
    <div class="{wrap_class}">
      <div class="contact-info">
        <p>I'm always open to new opportunities, collaborations, and interesting projects. Feel free to reach out!</p>
        <div class="contact-items">{contact_links}</div>
      </div>{contact_form}
    </div>
  </section>
'''

    # Render CSS and JS
    titles = [t for t in [title, 'Problem Solver', 'Creative Thinker'] if t]
    titles_json = json.dumps(titles).replace('</', '<\\/')
    email_json  = json.dumps(email).replace('</', '<\\/')

    css = render(CSS_TEMPLATE, {
        'BG': colors['bg'], 'BG2': colors['bg2'], 'BG3': colors['bg3'],
        'PRIMARY': colors['primary'], 'ON_PRIMARY': on_color(colors['primary']),
        'TEXT': colors['text'], 'TEXT2': colors['text2'], 'BORDER': colors['border'],
        'NAV_BG': f"rgba({rgb_string(colors['bg'])}, 0.88)",
        'ALT_BG': alt['bg'], 'ALT_BG2': alt['bg2'], 'ALT_BG3': alt['bg3'],
        'ALT_TEXT': alt['text'], 'ALT_TEXT2': alt['text2'], 'ALT_BORDER': alt['border'],
        'ALT_NAV_BG': f"rgba({rgb_string(alt['bg'])}, 0.88)",
        'FONT_SIZE': f'{round(font_scale * 100)}%',
        'FONT_NAME': font_name,
        'HERO_NAME_SIZE': hero_sizes.get(hero_size, hero_sizes['normal']),
        'PRIMARY_RGB': rgb_string(colors['primary']),
        'EXTRA_CSS': extra_css,
    })

    js = render(JS_TEMPLATE, {
        'TITLES_JSON': titles_json,
        'PARTICLE_COUNT': particle_counts.get(animations, 60),
        'PRIMARY_RGB': rgb_string(colors['primary']),
        'EMAIL_JSON': email_json,
    })

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(name)} - Portfolio</title>
  <link rel="stylesheet" href="{font_url}" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
  <style>
{css}
  </style>
</head>
<body>

  <nav>
    <a href="#hero" class="nav-logo">{esc(name_first)}</a>
    <ul class="nav-links">{nav_links}</ul>
    <div class="nav-right">
      {flip_button}
      <button class="hamburger" id="hamburger" aria-label="Menu" onclick="toggleMenu()"><span></span><span></span><span></span></button>
    </div>
  </nav>

  <div class="mobile-menu" id="mobile-menu">{mobile_links}</div>

  <section id="hero">
    <canvas id="hero-canvas"></canvas>
    <div class="hero-content">
      <div class="hero-text fade-in">
        <div class="hero-greeting">👋 Hello World</div>
        <h1 class="hero-name">{esc(name)}</h1>
        <div class="hero-title">I'm a <span id="typewriter"></span></div>
        <p class="hero-tagline">{esc(tagline)}</p>
        <div class="hero-btns">{hero_btns}</div>
        <div class="hero-social">{social}</div>
      </div>
      <div class="hero-photo-wrap fade-in">{hero_photo}</div>
    </div>
  </section>
{about_section}{skills_section}{projects_section}{contact_section}
  <footer>
    <p>Built with <span>❤️</span> by <span>{esc(name)}</span> · {datetime.datetime.now().year}</p>
  </footer>

  <button id="scroll-top" onclick="scrollTopNow()">↑</button>

  <script>
{js}
  </script>
</body>
</html>'''


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_file('index.html')


@app.route('/style.css')
def css_file():
    return send_file('style.css')


@app.route('/script.js')
def js_file():
    return send_file('script.js')


@app.route('/generate', methods=['POST'])
def generate():
    form = request.get_json() or {}

    name  = (form.get('name') or '').strip()
    title = (form.get('title') or '').strip()
    if not name or not title:
        return jsonify({'error': 'Name and title are required'}), 400

    overrides = {}

    # AI writes just a short tagline (if it fails, the page uses a default one)
    if GROQ_API_KEY:
        about = form.get('bio') or form.get('skills') or title
        try:
            text = call_groq(
                f'Write ONE short punchy tagline (max 15 words) for the portfolio website of {name}, a {title}. '
                f'About them: {about}. Return ONLY the tagline text, no quotes.',
                max_tokens=300, temperature=0.8, timeout=20,
            )
            tagline = text.splitlines()[0].strip().strip('"').strip("'") if text else ''
            if tagline:
                overrides['tagline'] = tagline[:160]
        except Exception as e:
            print('Tagline skipped:', e)

    html = build_portfolio_html(form, overrides)
    return jsonify({'html': html, 'overrides': overrides, 'success': True})


@app.route('/edit', methods=['POST'])
def edit():
    data         = request.get_json() or {}
    form         = data.get('form') or {}
    current      = clean_overrides(data.get('overrides'))
    request_text = (data.get('changes') or '').strip()

    if not form.get('name') or not request_text:
        return jsonify({'error': 'Missing portfolio data or edit request'}), 400

    prompt = (EDIT_PROMPT
              .replace('__CURRENT__', json.dumps(current))
              .replace('__REQUEST__', request_text[:500]))

    try:
        parsed = extract_json(call_groq(prompt, max_tokens=700, temperature=0.2))
    except Exception as e:
        return jsonify({'error': f'Could not understand that edit: {e}'}), 500

    changes = clean_overrides(parsed.get('changes'))

    if not changes:
        reason = parsed.get('unsupported') or "I couldn't turn that into a change I can apply safely. Try colors, fonts, text size, animations, themes, hiding sections, or a new tagline/bio."
        return jsonify({'unsupported': reason})

    overrides = merge_overrides(current, changes)
    html      = build_portfolio_html(form, overrides)

    return jsonify({
        'html':      html,
        'overrides': overrides,
        'summary':   parsed.get('summary') or 'Changes applied',
        'success':   True,
    })


SCORE_PROMPT = """You are a recruiter reviewing a developer portfolio website. Below is the visible text of the page.

Person: __NAME__
Page text:
__TEXT__

Score it honestly with whole numbers from 0 to 100. You only see text, so judge content, not visual design.
Reply with ONLY this JSON shape:
{
  "overall": <number>,
  "categories": {
    "content": {"score": <number>, "feedback": "<one short sentence>"},
    "clarity": {"score": <number>, "feedback": "<one short sentence>"},
    "projects": {"score": <number>, "feedback": "<one short sentence>"},
    "completeness": {"score": <number>, "feedback": "<one short sentence>"},
    "recruiter_appeal": {"score": <number>, "feedback": "<one short sentence>"}
  },
  "strengths": ["<text>", "<text>", "<text>"],
  "improvements": ["<text>", "<text>", "<text>"],
  "verdict": "<two short sentences>"
}"""


@app.route('/score', methods=['POST'])
def score():
    data      = request.get_json() or {}
    page_text = html_to_text(data.get('html', ''))[:2500]
    name      = data.get('name') or 'this person'

    if not page_text:
        return jsonify({'error': 'No portfolio to score'}), 400

    prompt = SCORE_PROMPT.replace('__NAME__', name).replace('__TEXT__', page_text)

    try:
        return jsonify(extract_json(call_groq(prompt, max_tokens=900, temperature=0.3, timeout=45)))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cover-letter', methods=['POST'])
def cover_letter():
    data      = request.get_json() or {}
    name      = data.get('name', '')
    title     = data.get('title', '')
    skills    = data.get('skills', '')
    projects  = data.get('projects') or []
    company   = data.get('company', 'the company')
    job_title = data.get('job_title', title)
    tone      = data.get('tone', 'professional')

    if not name:
        return jsonify({'error': 'Missing data'}), 400

    projects_text = ', '.join(p.get('name', '') for p in projects if p.get('name'))

    prompt = (f'Write a {tone} cover letter for {name} ({title}) applying to {company} for the role of {job_title}.\n'
              f'Skills: {skills}\nNotable projects: {projects_text}\n'
              'Use 3-4 paragraphs. Sound human and genuine, not generic. Return ONLY the cover letter text.')

    try:
        return jsonify({'letter': call_groq(prompt, max_tokens=900, temperature=0.8), 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/video-script', methods=['POST'])
def video_script():
    data     = request.get_json() or {}
    name     = data.get('name', '')
    title    = data.get('title', '')
    skills   = data.get('skills', '')
    projects = data.get('projects') or []
    duration = data.get('duration', '60')

    if not name:
        return jsonify({'error': 'Missing data'}), 400

    projects_text = '\n'.join(f"- {p.get('name', '')}: {p.get('desc', '')}" for p in projects if p.get('name'))

    prompt = (f'Write a {duration}-second portfolio video script for {name} ({title}).\n'
              f'Skills: {skills}\nProjects:\n{projects_text}\n'
              'Format with [INTRO] [ABOUT] [SKILLS] [PROJECTS] [CTA] sections. '
              'Include stage directions like [smile] [pause]. Return ONLY the script.')

    try:
        return jsonify({'script': call_groq(prompt, max_tokens=800, temperature=0.8), 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/saves', methods=['GET'])
def get_saves():
    return jsonify([
        {'id': s['id'], 'name': s['name'], 'title': s['title'], 'theme': s['theme'], 'created': s['created']}
        for s in load_saves()
    ])


@app.route('/saves', methods=['POST'])
def save_portfolio():
    data = request.get_json() or {}
    html = data.get('html', '')
    form = data.get('form', {})

    if not html:
        return jsonify({'error': 'No HTML'}), 400

    saves  = load_saves()
    new_id = max((s['id'] for s in saves), default=0) + 1

    saves.append({
        'id':      new_id,
        'name':    form.get('name', 'Untitled'),
        'title':   form.get('title', ''),
        'theme':   (form.get('overrides') or {}).get('theme') or form.get('theme', 'dark'),
        'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'html':    html,
        'form':    form,
    })

    write_saves(saves[-20:])
    return jsonify({'success': True, 'id': new_id})


@app.route('/saves/<int:save_id>', methods=['GET'])
def get_save(save_id):
    for s in load_saves():
        if s['id'] == save_id:
            return jsonify(s)
    return jsonify({'error': 'Not found'}), 404


@app.route('/saves/<int:save_id>', methods=['DELETE'])
def delete_save(save_id):
    write_saves([s for s in load_saves() if s['id'] != save_id])
    return jsonify({'success': True})


@app.route('/download', methods=['POST'])
def download():
    data     = request.get_json() or {}
    html     = data.get('html', '')
    filename = data.get('filename', 'portfolio.html')

    if not html:
        return jsonify({'error': 'No HTML'}), 400

    return Response(html, mimetype='text/html', headers={
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'text/html; charset=utf-8',
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, port=port)