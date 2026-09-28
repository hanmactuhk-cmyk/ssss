from pathlib import Path
import json, os
from .models import Account, save_json

ROOT = Path(os.environ.get('GLABS_AUTOMATION_HOME', Path.home() / 'G-Labs-Flow-Automation'))
DATA = ROOT / 'data'; PROFILES = ROOT / 'profiles'; OUTPUT = ROOT / 'output'; LOGS = ROOT / 'logs'
for p in (DATA, PROFILES, OUTPUT, LOGS): p.mkdir(parents=True, exist_ok=True)
ACCOUNTS = DATA / 'accounts.json'; SETTINGS = DATA / 'settings.json'

def load_accounts():
    if not ACCOUNTS.exists(): return []
    try: return [Account(**x) for x in json.loads(ACCOUNTS.read_text(encoding='utf-8'))]
    except Exception: return []

def save_accounts(items): save_json(ACCOUNTS, [a.__dict__ for a in items])

def load_settings():
    if not SETTINGS.exists(): return {}
    try: return json.loads(SETTINGS.read_text(encoding='utf-8'))
    except Exception: return {}

def save_settings(s): save_json(SETTINGS, s)
