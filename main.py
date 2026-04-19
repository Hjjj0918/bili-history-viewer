from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from bili_viewer.controller import AppController
from bili_viewer.logging_utils import setup_logging
from bili_viewer.view import MainWindow


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    # 持有控制器引用，避免被垃圾回收后导致信号槽失效。
    window.controller = AppController(window)  # type: ignore[attr-defined]
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
