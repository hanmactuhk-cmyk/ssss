from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import json, time

@dataclass
class Account:
    id: str
    name: str
    email: str = ""
    enabled: bool = True
    image_enabled: bool = True
    video_enabled: bool = True
    status: str = "READY"
    profile_dir: str = ""
    note: str = ""

@dataclass
class Job:
    id: str
    kind: str
    prompt: str
    model: str = ""
    aspect: str = "9:16"
    duration: str = "8"
    start_image: str = ""
    end_image: str = ""
    reference_images: list[str] = field(default_factory=list)
    output: str = ""
    status: str = "QUEUED"
    account_id: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self): return asdict(self)

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
