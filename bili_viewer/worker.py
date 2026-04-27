from __future__ import annotations

import logging
from typing import List, Set

from PySide6.QtCore import QThread, Signal

from .bilibili_client import BiliClient, BiliClientError, InvalidSESSDATAError, UIDNotFoundError
from .models import SpeechRecord


logger = logging.getLogger(__name__)


class FetchWorker(QThread):
    """在后台线程中执行网络抓取，避免阻塞 UI。"""

    success = Signal(list)
    error = Signal(str)
    progress = Signal(str)

    def __init__(
        self,
        uid: str,
        sessdata: str,
        enabled_sources: Set[str] | None = None,
    ) -> None:
        super().__init__()
        self.uid = uid.strip()
        self.sessdata = sessdata.strip()
        self.enabled_sources = enabled_sources or {"动态", "评论"}

    def run(self) -> None:
        try:
            self.progress.emit("正在初始化请求客户端...")
            client = BiliClient(sessdata=self.sessdata)

            records: List[SpeechRecord] = client.fetch_user_speeches(
                uid=self.uid,
                enabled_sources=self.enabled_sources,
                progress_callback=lambda msg: self.progress.emit(msg),
            )
            self.success.emit(records)
        except InvalidSESSDATAError as exc:
            logger.warning("SESSDATA 校验失败: %s", exc)
            self.error.emit(f"Cookie 失效：{exc}")
        except UIDNotFoundError as exc:
            logger.warning("UID 校验失败: uid=%s error=%s", self.uid, exc)
            self.error.emit(f"UID 错误：{exc}")
        except BiliClientError as exc:
            logger.exception("业务请求失败: uid=%s", self.uid)
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("后台线程出现未知异常: uid=%s", self.uid)
            self.error.emit(f"未知错误：{exc}")
