from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtWidgets import QFileDialog

from .models import SpeechRecord, export_to_csv, export_to_json
from .view import MainWindow
from .worker import FetchWorker


class AppController:
    """控制器：负责连接 UI 与业务逻辑。"""

    def __init__(self, view: MainWindow) -> None:
        self.view = view
        self.records: List[SpeechRecord] = []
        self.worker: FetchWorker | None = None

        self.view.query_btn.clicked.connect(self.on_query_clicked)
        self.view.export_csv_btn.clicked.connect(self.on_export_csv_clicked)
        self.view.export_json_btn.clicked.connect(self.on_export_json_clicked)

    def on_query_clicked(self) -> None:
        uid = self.view.uid_edit.text().strip()
        sessdata = self.view.sessdata_edit.text().strip()

        if not uid.isdigit():
            self.view.show_error("请填写合法的数字 UID。")
            return
        if not sessdata:
            self.view.show_error("请先输入 SESSDATA。")
            return

        self.view.set_loading(True, "开始查询...")
        self.records.clear()
        self.view.export_csv_btn.setEnabled(False)
        self.view.export_json_btn.setEnabled(False)

        self.worker = FetchWorker(uid=uid, sessdata=sessdata)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.success.connect(self.on_worker_success)
        self.worker.error.connect(self.on_worker_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_progress(self, message: str) -> None:
        self.view.status_label.setText(message)

    def on_worker_success(self, records: list[SpeechRecord]) -> None:
        self.records = records
        self.view.load_records(records)
        self.view.status_label.setText(f"查询完成，共 {len(records)} 条记录")

        has_data = len(records) > 0
        self.view.export_csv_btn.setEnabled(has_data)
        self.view.export_json_btn.setEnabled(has_data)

    def on_worker_error(self, message: str) -> None:
        self.view.show_error(message)
        self.view.status_label.setText("查询失败")

    def on_worker_finished(self) -> None:
        self.view.set_loading(False)

    def on_export_csv_clicked(self) -> None:
        if not self.records:
            self.view.show_error("暂无可导出的数据。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "导出 CSV",
            str(Path.cwd() / "bili_speeches.csv"),
            "CSV 文件 (*.csv)",
        )
        if not file_path:
            return

        try:
            export_to_csv(self.records, file_path)
            self.view.show_info("CSV 导出成功。")
        except Exception as exc:  # noqa: BLE001
            self.view.show_error(f"CSV 导出失败：{exc}")

    def on_export_json_clicked(self) -> None:
        if not self.records:
            self.view.show_error("暂无可导出的数据。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "导出 JSON",
            str(Path.cwd() / "bili_speeches.json"),
            "JSON 文件 (*.json)",
        )
        if not file_path:
            return

        try:
            export_to_json(self.records, file_path)
            self.view.show_info("JSON 导出成功。")
        except Exception as exc:  # noqa: BLE001
            self.view.show_error(f"JSON 导出失败：{exc}")
