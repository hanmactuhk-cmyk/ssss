from pathlib import Path
import json, time, uuid
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from ..models import Job, Account

class FlowRunner:
    def __init__(self, root: Path, selector_file: Path, log):
        self.root=root; self.selector_file=selector_file; self.log=log; self._stop=False; self._pause=False
        self.selectors=json.loads(selector_file.read_text(encoding='utf-8'))
        self.pw=None; self.browser=None; self.context=None; self.page=None

    def stop(self): self._stop=True
    def pause(self): self._pause=True
    def resume(self): self._pause=False

    def _first(self, locators, timeout=3000):
        for s in locators:
            try:
                loc=self.page.locator(s).first
                loc.wait_for(state='visible', timeout=timeout)
                return loc
            except Exception: pass
        return None

    def open_account(self, account: Account):
        self.close()
        self.pw=sync_playwright().start()
        profile=Path(account.profile_dir)
        profile.mkdir(parents=True, exist_ok=True)
        self.context=self.pw.chromium.launch_persistent_context(str(profile), headless=False, viewport={"width":1440,"height":900})
        self.page=self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto(self.selectors['flow_url'], wait_until='domcontentloaded', timeout=60000)
        self.log(f'Opened Flow with profile {account.name}')
        time.sleep(2)
        if self._first(self.selectors.get('captcha_or_login',[]), 1200):
            raise RuntimeError('Flow yêu cầu đăng nhập/xác minh/CAPTCHA. Hãy xử lý thủ công rồi chạy lại tài khoản này.')

    def run_job(self, job: Job, account: Account):
        if self._stop: raise RuntimeError('STOPPED')
        if not self.page: self.open_account(account)
        while self._pause and not self._stop: time.sleep(.25)
        if self._stop: raise RuntimeError('STOPPED')
        self.page.goto(self.selectors['flow_url'], wait_until='domcontentloaded', timeout=60000)
        time.sleep(1.5)
        tab_key='video_tab' if job.kind=='video' else 'image_tab'
        tab=self._first(self.selectors.get(tab_key,[]),2500)
        if tab: 
            try: tab.click()
            except Exception: pass
        prompt=self._first(self.selectors['prompt'],5000)
        if not prompt: raise RuntimeError('Không tìm thấy ô Prompt. Hãy cập nhật data/flow_selectors.json.')
        prompt.fill(job.prompt)
        btn=self._first(self.selectors['generate'],5000)
        if not btn: raise RuntimeError('Không tìm thấy nút Create/Generate.')
        btn.click()
        self.log(f'{job.kind}: submitted {job.id}')
        # Wait for a downloadable result. The exact Flow UI can vary, so keep this generic.
        deadline=time.time()+1800
        while time.time()<deadline:
            if self._stop: raise RuntimeError('STOPPED')
            while self._pause and not self._stop: time.sleep(.25)
            dl=self._first(self.selectors.get('download',[]),1000)
            if dl:
                try:
                    with self.page.expect_download(timeout=3000) as dlinfo:
                        dl.click()
                    download=dlinfo.value
                    out=Path(job.output)
                    out.parent.mkdir(parents=True,exist_ok=True)
                    download.save_as(str(out))
                    return str(out)
                except Exception: pass
            time.sleep(3)
        raise RuntimeError('Timeout chờ kết quả Flow.')

    def close(self):
        try:
            if self.context: self.context.close()
        except Exception: pass
        try:
            if self.pw: self.pw.stop()
        except Exception: pass
        self.context=self.page=self.pw=None
