"""Headless check + screenshots of the built demo. Usage: python scripts/shots.py <url> <outdir>
Fails (rc 1) on a Python exception box, console errors from the app, or horizontal scroll at 390px."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

url, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
PAGES = ["overview", "leads", "students", "contracts", "schedule", "finance"]
bad = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for tag, vw, vh in (("desktop", 1366, 800), ("mobile", 390, 844)):
        pg = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=2 if tag == "mobile" else 1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="domcontentloaded")
        pg.wait_for_selector('[data-testid="stMain"] h1', timeout=150000)
        for name in PAGES:
            if name != "overview":
                if tag == "desktop":
                    pg.locator(f'[data-testid="stSidebar"] a[href*="{name}"]').first.click()
                else:
                    link = pg.locator(f'[data-testid="stSidebar"] a[href*="{name}"]').first
                    if pg.locator('[data-testid="stSidebar"]').get_attribute('aria-expanded') != 'true':
                        pg.locator('[data-testid="stExpandSidebarButton"]').first.click()
                    link.click(timeout=15000)
                    pg.locator('[data-testid="stSidebarCollapseButton"] button').first.click()
                pg.wait_for_timeout(2500)
            pg.wait_for_selector('[data-testid="stMain"] h1', timeout=60000)
            pg.wait_for_timeout(2500)
            if pg.locator('[data-testid="stException"]').count():
                bad.append(f"{tag}/{name}: exception box")
            ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if tag == "mobile" and ov > 0:
                bad.append(f"{tag}/{name}: horizontal overflow {ov}px")
            pg.screenshot(path=str(out / f"{tag}-{name}.png"), full_page=(tag == "desktop"))
        bad += [f"{tag}: pageerror {e[:200]}" for e in errs]
        pg.close()
    b.close()
print("PROBLEMS:" if bad else "OK", *bad, sep="\n")
sys.exit(1 if bad else 0)
