from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
from typing import Iterable, List


@dataclass(slots=True)
class SpeechRecord:
    """统一表示一条“发言”记录。"""

    source_type: str
    content: str
    publish_time: str
    source_title: str
    source_url: str


def export_to_csv(records: Iterable[SpeechRecord], file_path: str) -> None:
    """导出为 CSV。"""
    path = Path(file_path)
    field_names = ["source_type", "content", "publish_time", "source_title", "source_url"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for item in records:
            writer.writerow(asdict(item))


def export_to_json(records: Iterable[SpeechRecord], file_path: str) -> None:
    """导出为 JSON。"""
    path = Path(file_path)
    payload: List[dict] = [asdict(item) for item in records]
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
