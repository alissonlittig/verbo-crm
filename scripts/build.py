"""Build dist/index.html: the Streamlit app in app/ embedded for stlite (Pyodide), no server needed."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STLITE = "1.12.1"
files = {p.name: p.read_text(encoding="utf-8") for p in sorted((ROOT / "app").glob("*.py"))}
cfg = {
    "entrypoint": "streamlit_app.py",
    "requirements": [],
    "streamlitConfig": {"client.toolbarMode": "viewer", "theme.base": "light", "theme.primaryColor": "#FF6B5B",
                        "theme.backgroundColor": "#F6F3EC", "theme.secondaryBackgroundColor": "#FFFFFF",
                        "theme.textColor": "#15152B"},
    "files": files,
}
blob = json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/")
html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verbo CRM — language school demo</title>
<meta name="description" content="A CRM for a language school in Python: lead funnel, students, contracts, schedule and DRE. Runs entirely in your browser.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='9' fill='%23FF6B5B'/%3E%3C/svg%3E">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE}/build/stlite.css">
<style>html,body{{margin:0;background:#F6F3EC}}#boot{{position:fixed;inset:0;display:grid;place-content:center;gap:.6rem;text-align:center;font:500 15px Inter,system-ui,sans-serif;color:#15152B;pointer-events:none}}#boot b{{font:700 28px Georgia,serif}}#boot span{{color:#6B6B80;font-size:13px}}</style>
</head>
<body>
<div id="boot"><b>Verbo</b>Starting Python in your browser…<span>First load takes about 20 seconds</span></div>
<div id="root"></div>
<script type="module">
import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE}/build/stlite.js";
mount({blob}, document.getElementById("root"));
new MutationObserver((_, o) => {{ if (document.querySelector('[data-testid="stApp"],.stApp')) {{ document.getElementById("boot")?.remove(); o.disconnect(); }} }})
  .observe(document.body, {{ childList: true, subtree: true }});
</script>
<noscript>This demo needs JavaScript.</noscript>
</body>
</html>
"""
out = ROOT / "dist"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
(out / ".nojekyll").write_text("")
print(f"built dist/index.html ({len(html) // 1024} KB, {len(files)} python files)")
sys.exit(0)
