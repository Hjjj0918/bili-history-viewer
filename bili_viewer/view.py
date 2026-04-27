from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import SpeechRecord


class MainWindow(QMainWindow):
    """主界面。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Bilibili UID 历史发言查看器")
        self.resize(1100, 700)

        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # 输入区域
        form_box = QGroupBox("查询参数")
        form_layout = QGridLayout(form_box)

        self.uid_edit = QLineEdit()
        self.uid_edit.setPlaceholderText("输入目标 UID，例如：2")

        self.sessdata_edit = QLineEdit()
        self.sessdata_edit.setPlaceholderText("输入你自己的 SESSDATA")
        self.sessdata_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.query_btn = QPushButton("开始查询")
        self.export_csv_btn = QPushButton("导出 CSV")
        self.export_json_btn = QPushButton("导出 JSON")

        self.export_csv_btn.setEnabled(False)
        self.export_json_btn.setEnabled(False)

        form_layout.addWidget(QLabel("目标 UID:"), 0, 0)
        form_layout.addWidget(self.uid_edit, 0, 1)
        form_layout.addWidget(QLabel("SESSDATA:"), 1, 0)
        form_layout.addWidget(self.sessdata_edit, 1, 1)

        # 数据源选择
        sources_label = QLabel("数据源:")
        form_layout.addWidget(sources_label, 2, 0)

        sources_layout = QHBoxLayout()
        self.cb_dynamics = QCheckBox("空间动态")
        self.cb_comments = QCheckBox("视频评论")
        self.cb_favorites = QCheckBox("收藏夹")
        self.cb_likes = QCheckBox("点赞视频")
        self.cb_followings = QCheckBox("关注列表")
        self.cb_followers = QCheckBox("粉丝列表")
        self.cb_live = QCheckBox("直播间发言")

        self.cb_dynamics.setChecked(True)
        self.cb_comments.setChecked(True)

        sources_layout.addWidget(self.cb_dynamics)
        sources_layout.addWidget(self.cb_comments)
        sources_layout.addWidget(self.cb_favorites)
        sources_layout.addWidget(self.cb_likes)
        sources_layout.addWidget(self.cb_followings)
        sources_layout.addWidget(self.cb_followers)
        sources_layout.addWidget(self.cb_live)
        sources_layout.addStretch(1)

        form_layout.addLayout(sources_layout, 2, 1)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.query_btn)
        button_layout.addWidget(self.export_csv_btn)
        button_layout.addWidget(self.export_json_btn)
        button_layout.addStretch(1)

        form_layout.addLayout(button_layout, 3, 0, 1, 2)

        # 状态区域
        status_layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)

        status_layout.addWidget(QLabel("状态:"))
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)

        # 结果表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["类型", "内容", "发布时间", "来源标题", "来源链接"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        root_layout.addWidget(form_box)
        root_layout.addLayout(status_layout)
        root_layout.addWidget(self.table)

    def set_loading(self, loading: bool, tip: str = "") -> None:
        self.progress_bar.setVisible(loading)
        self.progress_bar.setRange(0, 0 if loading else 1)
        self.progress_bar.setValue(0)
        self.query_btn.setEnabled(not loading)
        if tip:
            self.status_label.setText(tip)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "错误", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "提示", message)

    def load_records(self, records: list[SpeechRecord]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(records))

        for row, item in enumerate(records):
            col0 = QTableWidgetItem(item.source_type)
            col1 = QTableWidgetItem(item.content)
            col2 = QTableWidgetItem(item.publish_time)
            col3 = QTableWidgetItem(item.source_title)
            col4 = QTableWidgetItem(item.source_url)
            col4.setFlags(col4.flags() ^ Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(row, 0, col0)
            self.table.setItem(row, 1, col1)
            self.table.setItem(row, 2, col2)
            self.table.setItem(row, 3, col3)
            self.table.setItem(row, 4, col4)

        self.table.setSortingEnabled(True)
