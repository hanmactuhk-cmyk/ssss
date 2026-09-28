from PySide6.QtCore import QThread, Signal
from pathlib import Path
import time, traceback
from .browser.flow_runner import FlowRunner
from .models import Job, Account

class QueueWorker(QThread):
    job_signal=Signal(str,str,str); log_signal=Signal(str); finished_signal=Signal(); account_signal=Signal(str,str)
    def __init__(self, root, jobs, accounts, selector_file):
        super().__init__(); self.root=root; self.jobs=jobs; self.accounts=accounts; self.selector_file=selector_file; self.stop_flag=False; self.pause_flag=False; self.runner=None
    def stop(self): self.stop_flag=True; self.runner and self.runner.stop()
    def pause(self): self.pause_flag=True; self.runner and self.runner.pause()
    def resume(self): self.pause_flag=False; self.runner and self.runner.resume()
    def run(self):
        self.runner=FlowRunner(self.root,self.selector_file,self.log)
        try:
            ai=0
            for job in self.jobs:
                if self.stop_flag: break
                while self.pause_flag and not self.stop_flag: time.sleep(.2)
                usable=[a for a in self.accounts if a.enabled and ((job.kind=='video' and a.video_enabled) or (job.kind=='image' and a.image_enabled)) and a.status not in ('DISABLED','BLOCKED')]
                if not usable: self.log('Không còn tài khoản khả dụng.'); break
                account=usable[ai % len(usable)]; ai+=1; job.account_id=account.id
                self.account_signal.emit(account.id,'RUNNING'); self.job_signal.emit(job.id,'RUNNING',account.name)
                try:
                    if not account.profile_dir: raise RuntimeError('Thiếu Chrome profile.')
                    out=job.output or str(self.root/'output'/(job.id + ('.mp4' if job.kind=='video' else '.png')))
                    job.output=out
                    result=self.runner.run_job(job,account)
                    job.status='DONE'; self.job_signal.emit(job.id,'DONE',result); account.status='READY'
                except Exception as e:
                    job.status='ERROR'; job.error=str(e); self.job_signal.emit(job.id,'ERROR',str(e)); account.status='READY' if 'STOPPED' not in str(e) else 'READY'; self.log(f'{job.id}: {e}')
                self.account_signal.emit(account.id,account.status)
        finally:
            self.runner.close(); self.finished_signal.emit()
    def log(self,s): self.log_signal.emit(s)
