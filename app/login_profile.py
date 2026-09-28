import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
p=Path(sys.argv[1]); p.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(str(p),headless=False,viewport={'width':1440,'height':900})
    page=ctx.pages[0] if ctx.pages else ctx.new_page(); page.goto('https://flow.google.com/',wait_until='domcontentloaded',timeout=60000)
    print('Đăng nhập Google trong cửa sổ này. Đóng cửa sổ để kết thúc.')
    try: page.wait_for_timeout(3600000)
    except: pass
    ctx.close()
