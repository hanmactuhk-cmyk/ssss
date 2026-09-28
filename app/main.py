from __future__ import annotations
import sys, uuid, json, subprocess
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from .models import Job, Account, save_json
from .storage import ROOT, PROFILES, OUTPUT, load_accounts, save_accounts, load_settings, save_settings
from .worker import QueueWorker

APP_TITLE='G-Labs Flow Automation v4'

class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(APP_TITLE); self.resize(1380,900)
        self.accounts=load_accounts(); self.settings=load_settings(); self.jobs=[]; self.worker=None
        self.tabs=QTabWidget(); self.tabs.setTabPosition(QTabWidget.West); self.setCentralWidget(self.tabs)
        self._make_tabs(); self.refresh_accounts(); self.apply_style()
    def apply_style(self):
        self.setStyleSheet('''QMainWindow,QWidget{background:#171a20;color:#e7eaf0} QGroupBox{border:1px solid #303642;border-radius:8px;margin-top:8px;padding:12px} QGroupBox::title{left:12px;padding:0 5px} QPushButton{background:#28303c;border:1px solid #3a4352;border-radius:6px;padding:8px 12px} QPushButton:hover{background:#344054} QLineEdit,QTextEdit,QComboBox,QTableWidget,QListWidget{background:#20252e;color:#f1f3f6;border:1px solid #343c49;border-radius:6px;padding:5px} QHeaderView::section{background:#262c36;color:#ddd;padding:6px} QTabBar::tab{padding:12px 18px}''')
    def add_page(self,name,w): self.tabs.addTab(w,name)
    def _make_tabs(self):
        self.add_page('Flow Ảnh', self.image_page()); self.add_page('Flow Video',self.video_page()); self.add_page('Nhân vật',self.character_page()); self.add_page('GPT Image 2',self.simple_page('GPT Image 2')); self.add_page('Meta Media',self.simple_page('Meta Media')); self.add_page('Grok Media',self.simple_page('Grok Media')); self.add_page('Workflow',self.workflow_page()); self.add_page('Dựng Video',self.editor_page()); self.add_page('Nâng cấp Ảnh',self.upscale_page()); self.add_page('Tài khoản Flow',self.accounts_page()); self.add_page('Log Chi Tiết',self.logs_page()); self.add_page('Cài đặt',self.settings_page())
    def base_prompt_page(self,kind):
        w=QWidget(); l=QVBoxLayout(w); cfg=QGroupBox('Cấu hình cơ bản'); f=QGridLayout(cfg)
        model=QComboBox(); model.addItems(['Lite','Fast','Quality','Relaxed','Auto']); aspect=QComboBox(); aspect.addItems(['9:16 Doc','16:9 Ngang','1:1 Vuông']); duration=QComboBox(); duration.addItems(['5','7','8','10']); concurrency=QSpinBox(); concurrency.setRange(1,30); concurrency.setValue(1); delay=QSpinBox(); delay.setRange(0,3600); delay.setValue(0)
        f.addWidget(QLabel('Model:'),0,0); f.addWidget(model,0,1); f.addWidget(QLabel('Tỷ lệ:'),0,2); f.addWidget(aspect,0,3); f.addWidget(QLabel('Thời lượng:'),1,0); f.addWidget(duration,1,1); f.addWidget(QLabel('Hàng đồng thời:'),1,2); f.addWidget(concurrency,1,3); f.addWidget(QLabel('Chờ giữa task (giây):'),2,0); f.addWidget(delay,2,1)
        l.addWidget(cfg)
        box=QGroupBox('Prompt / Hàng chờ'); bl=QVBoxLayout(box); self.prompt=QTextEdit(); self.prompt.setPlaceholderText('Nhập mỗi prompt một dòng hoặc dùng ô này cho prompt đơn...'); bl.addWidget(self.prompt); row=QHBoxLayout(); add=QPushButton('+ Thêm vào hàng chờ'); add.clicked.connect(lambda:self.add_prompts(kind,model.currentText(),aspect.currentText().split()[0],duration.currentText())); imp=QPushButton('Nhập TXT'); imp.clicked.connect(self.import_txt); clear=QPushButton('Xóa hàng'); clear.clicked.connect(lambda:self.jobs.clear() or self.refresh_jobs()); row.addWidget(add);row.addWidget(imp);row.addWidget(clear); bl.addLayout(row); l.addWidget(box)
        self.job_table=QTableWidget(0,6); self.job_table.setHorizontalHeaderLabels(['ID','Loại','Prompt','Tài khoản','Trạng thái','Kết quả']); self.job_table.horizontalHeader().setStretchLastSection(True); l.addWidget(self.job_table,1)
        br=QHBoxLayout(); run=QPushButton('▶ CHẠY NGAY'); run.clicked.connect(self.start); pause=QPushButton('TẠM DỪNG'); pause.clicked.connect(self.pause); stop=QPushButton('DỪNG'); stop.clicked.connect(self.stop); br.addWidget(run);br.addWidget(pause);br.addWidget(stop); l.addLayout(br)
        return w
    def video_page(self): return self.base_prompt_page('video')
    def image_page(self): return self.base_prompt_page('image')
    def add_prompts(self,kind,model,aspect,duration):
        lines=[x.strip() for x in self.prompt.toPlainText().splitlines() if x.strip()]
        for p in lines: self.jobs.append(Job(uuid.uuid4().hex[:8],kind,p,model,aspect,duration,output=''))
        self.refresh_jobs(); self.prompt.clear(); self.log(f'Đã thêm {len(lines)} task.')
    def import_txt(self):
        p,_=QFileDialog.getOpenFileName(self,'Nhập TXT','','Text (*.txt);;CSV (*.csv)');
        if p: self.prompt.setPlainText(Path(p).read_text(encoding='utf-8',errors='ignore'))
    def refresh_jobs(self):
        if not hasattr(self,'job_table'): return
        self.job_table.setRowCount(0)
        for j in self.jobs:
            r=self.job_table.rowCount(); self.job_table.insertRow(r); vals=[j.id,j.kind,j.prompt[:80],j.account_id,j.status,j.output or j.error]
            for c,v in enumerate(vals): self.job_table.setItem(r,c,QTableWidgetItem(str(v)))
    def accounts_page(self):
        w=QWidget(); l=QVBoxLayout(w); info=QLabel('Đăng nhập Google một lần trong Chrome profile riêng. Không lưu mật khẩu.'); l.addWidget(info); b=QHBoxLayout(); add=QPushButton('+ Thêm tài khoản'); add.clicked.connect(self.add_account); remove=QPushButton('Xóa'); remove.clicked.connect(self.remove_account); login=QPushButton('Mở đăng nhập'); login.clicked.connect(self.login_selected); toggle=QPushButton('Bật/Tắt'); toggle.clicked.connect(self.toggle_account); b.addWidget(add);b.addWidget(remove);b.addWidget(login);b.addWidget(toggle); l.addLayout(b); self.account_table=QTableWidget(0,8); self.account_table.setHorizontalHeaderLabels(['#','Tên','Gmail','Ảnh','Video','Trạng thái','Profile','Ghi chú']); self.account_table.horizontalHeader().setStretchLastSection(True); l.addWidget(self.account_table); return w
    def refresh_accounts(self):
        if not hasattr(self,'account_table'): return
        self.account_table.setRowCount(0)
        for i,a in enumerate(self.accounts,1):
            r=self.account_table.rowCount(); self.account_table.insertRow(r); vals=[i,a.name,a.email,'✓' if a.image_enabled else '', '✓' if a.video_enabled else '',a.status,a.profile_dir,a.note]
            for c,v in enumerate(vals): self.account_table.setItem(r,c,QTableWidgetItem(str(v)))
    def add_account(self):
        name,ok=QInputDialog.getText(self,'Tài khoản Flow','Tên profile:');
        if not ok or not name.strip(): return
        aid=uuid.uuid4().hex[:8]; profile=str(PROFILES/aid); a=Account(aid,name.strip(),profile_dir=profile); self.accounts.append(a); save_accounts(self.accounts); self.refresh_accounts(); self.open_profile(a)
    def selected_account(self):
        r=self.account_table.currentRow(); return self.accounts[r] if r>=0 and r<len(self.accounts) else None
    def open_profile(self,a):
        try: subprocess.Popen([sys.executable,'-m','app.login_profile',a.profile_dir])
        except Exception as e: QMessageBox.critical(self,'Lỗi',str(e))
    def login_selected(self):
        a=self.selected_account();
        if a: self.open_profile(a)
    def remove_account(self):
        a=self.selected_account();
        if not a:return
        self.accounts=[x for x in self.accounts if x.id!=a.id]; save_accounts(self.accounts); self.refresh_accounts()
    def toggle_account(self):
        a=self.selected_account();
        if a: a.enabled=not a.enabled; a.status='READY' if a.enabled else 'DISABLED'; save_accounts(self.accounts); self.refresh_accounts()
    def character_page(self):
        w=QWidget(); l=QVBoxLayout(w); add=QPushButton('+ Thêm nhân vật / ảnh tham chiếu'); add.clicked.connect(self.add_character); l.addWidget(add); self.char_list=QListWidget(); l.addWidget(self.char_list); return w
    def add_character(self):
        p,_=QFileDialog.getOpenFileName(self,'Chọn ảnh','','Images (*.png *.jpg *.jpeg *.webp)');
        if p: self.char_list.addItem(p)
    def simple_page(self,name):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel(f'{name} — mô-đun sẵn sàng để cấu hình engine tương ứng.')); t=QTextEdit(); t.setPlaceholderText('Prompt...'); l.addWidget(t); b=QPushButton('Thêm vào hàng chờ'); b.clicked.connect(lambda:self.log(f'{name}: prompt added')); l.addWidget(b); return w
    def workflow_page(self):
        w=QWidget(); l=QVBoxLayout(w); self.workflow_edit=QTextEdit(); self.workflow_edit.setPlainText('{\n  "name": "My Workflow",\n  "jobs": []\n}'); l.addWidget(self.workflow_edit); b=QHBoxLayout(); save=QPushButton('Lưu Workflow'); save.clicked.connect(self.save_workflow); load=QPushButton('Mở Workflow'); load.clicked.connect(self.load_workflow); b.addWidget(save);b.addWidget(load);l.addLayout(b);return w
    def save_workflow(self):
        p,_=QFileDialog.getSaveFileName(self,'Lưu workflow','','JSON (*.json)');
        if p: Path(p).write_text(self.workflow_edit.toPlainText(),encoding='utf-8')
    def load_workflow(self):
        p,_=QFileDialog.getOpenFileName(self,'Mở workflow','','JSON (*.json)');
        if p:self.workflow_edit.setPlainText(Path(p).read_text(encoding='utf-8'))
    def editor_page(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel('Dựng Video')); self.video_list=QListWidget(); l.addWidget(self.video_list); b=QPushButton('Thêm video'); b.clicked.connect(self.add_video); l.addWidget(b); return w
    def add_video(self):
        p,_=QFileDialog.getOpenFileName(self,'Chọn video','','Video (*.mp4 *.mov *.webm)');
        if p:self.video_list.addItem(p)
    def upscale_page(self):
        w=QWidget(); l=QVBoxLayout(w); self.up_file=QLineEdit(); b=QPushButton('Chọn ảnh'); b.clicked.connect(lambda:self.up_file.setText(QFileDialog.getOpenFileName(self,'Ảnh','','Images (*.png *.jpg *.jpeg *.webp)')[0])); go=QPushButton('Mở xử lý'); go.clicked.connect(lambda:self.log('Upscale: đã chọn ảnh '+self.up_file.text())); l.addWidget(self.up_file);l.addWidget(b);l.addWidget(go);return w
    def logs_page(self):
        w=QWidget(); l=QVBoxLayout(w); self.log_box=QPlainTextEdit(); self.log_box.setReadOnly(True); l.addWidget(self.log_box); return w
    def settings_page(self):
        w=QWidget(); f=QFormLayout(w); self.sel=QLineEdit(str(ROOT/'data'/'flow_selectors.json')); self.out=QLineEdit(str(OUTPUT)); self.poll=QSpinBox(); self.poll.setRange(1,60); self.poll.setValue(3); f.addRow('Selector file',self.sel);f.addRow('Output',self.out);f.addRow('Polling (giây)',self.poll); b=QPushButton('Lưu');b.clicked.connect(lambda:save_settings({'selector_file':self.sel.text(),'output':self.out.text(),'poll':self.poll.value()}));f.addRow(b);return w
    def start(self):
        if self.worker and self.worker.isRunning(): return
        if not self.jobs: QMessageBox.warning(self,'Hàng chờ','Chưa có task.'); return
        if not any(a.enabled for a in self.accounts): QMessageBox.warning(self,'Tài khoản','Chưa có tài khoản Flow.'); return
        for j in self.jobs:
            if not j.output: j.output=str(Path(self.out.text())/(j.id+('.mp4' if j.kind=='video' else '.png')))
        self.worker=QueueWorker(ROOT,self.jobs,self.accounts,Path(self.sel.text())); self.worker.job_signal.connect(self.on_job); self.worker.log_signal.connect(self.log); self.worker.account_signal.connect(self.on_account); self.worker.finished_signal.connect(lambda:self.log('Đã kết thúc hàng chờ')); self.worker.start(); self.log('Bắt đầu chạy tự động.')
    def pause(self):
        if self.worker: self.worker.pause()
    def stop(self):
        if self.worker: self.worker.stop()
    def on_job(self,jid,status,info):
        for j in self.jobs:
            if j.id==jid:j.status=status; j.account_id=info if status=='RUNNING' else j.account_id
        self.refresh_jobs()
    def on_account(self,aid,status):
        for a in self.accounts:
            if a.id==aid:a.status=status
        save_accounts(self.accounts); self.refresh_accounts()
    def log(self,s):
        if hasattr(self,'log_box'): self.log_box.appendPlainText(s)
        print(s)

if __name__=='__main__':
    app=QApplication(sys.argv); win=Main(); win.show(); sys.exit(app.exec())
