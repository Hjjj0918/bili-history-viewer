from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any, Dict, List, Optional

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from .models import SpeechRecord


logger = logging.getLogger(__name__)


class BiliClientError(Exception):
    """Bilibili API 调用错误。"""


class InvalidSESSDATAError(BiliClientError):
    """SESSDATA 失效或不可用。"""


class UIDNotFoundError(BiliClientError):
    """UID 不存在。"""


class BiliClient:
    """B 站请求客户端。

    注意：B 站并未公开“按 UID 全站检索所有评论”的官方接口。
    本工具采用“空间动态 + 目标用户投稿视频评论区过滤”的方式进行近似检索。
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    ]

    @staticmethod
    def _normalize_sessdata(raw_input: str) -> str:
        """兼容“仅值”与“整串 Cookie”两种输入，并校验编码安全性。"""
        text = (raw_input or "").strip()
        if not text:
            raise InvalidSESSDATAError("SESSDATA 为空，请重新输入。")

        # 支持用户直接粘贴整串 Cookie：优先从中提取 SESSDATA。
        if "SESSDATA=" in text:
            cookie = SimpleCookie()
            try:
                cookie.load(text)
            except Exception:
                # 非标准 Cookie 字符串时，降级做手工切分。
                pieces = [p.strip() for p in text.split(";") if p.strip()]
                sess_value = ""
                for p in pieces:
                    if p.startswith("SESSDATA="):
                        sess_value = p.split("=", 1)[1].strip()
                        break
            else:
                sess = cookie.get("SESSDATA")
                sess_value = sess.value.strip() if sess else ""
        else:
            sess_value = text

        if not sess_value:
            raise InvalidSESSDATAError("未在输入中找到有效的 SESSDATA。")

        # requests/urllib3 的请求头走 latin-1，Cookie 值若含中文会直接抛编码错误。
        if not sess_value.isascii():
            raise InvalidSESSDATAError(
                "SESSDATA 含有非 ASCII 字符，请只粘贴浏览器 Cookie 的原始值，不要包含中文说明或引号。"
            )

        return sess_value

    def __init__(self, sessdata: str, timeout: int = 12) -> None:
        self.session = requests.Session()
        self.timeout = timeout
        self.sessdata = self._normalize_sessdata(sessdata)
        self.session.cookies.set("SESSDATA", self.sessdata)
        self.session.headers.update(
            {
                "Referer": "https://www.bilibili.com/",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.bilibili.com",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "DNT": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            }
        )

    def _warmup_session(self) -> None:
        """先访问首页，让服务端下发常见风控相关 Cookie。"""
        try:
            self.session.headers["User-Agent"] = random.choice(self.USER_AGENTS)
            self.session.get("https://www.bilibili.com/", timeout=self.timeout)
        except RequestException:
            # 预热失败不阻断主流程。
            logger.exception("会话预热失败")
            return

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发起请求并统一处理常见异常。"""
        # 对临时风控做短重试与退避，减少 412 直接失败。
        for attempt in range(3):
            self.session.headers["User-Agent"] = random.choice(self.USER_AGENTS)

            try:
                resp: Response = self.session.get(url, params=params, timeout=self.timeout)
                logger.info("请求接口: url=%s status=%s", resp.url, resp.status_code)
            except Timeout as exc:
                logger.exception("请求超时: url=%s params=%s attempt=%s", url, params, attempt + 1)
                if attempt < 2:
                    time.sleep(random.uniform(0.8, 1.6))
                    continue
                raise BiliClientError("请求超时，请稍后重试。") from exc
            except RequestException as exc:
                logger.exception("请求异常: url=%s params=%s attempt=%s", url, params, attempt + 1)
                if attempt < 2:
                    time.sleep(random.uniform(0.8, 1.6))
                    continue
                raise BiliClientError(f"网络请求失败：{exc}") from exc

            if resp.status_code == 412:
                if attempt == 0:
                    self._warmup_session()
                if attempt < 2:
                    logger.warning("接口触发 412 风控，准备重试: url=%s attempt=%s", url, attempt + 1)
                    time.sleep(random.uniform(1.0, 2.0))
                    continue
                logger.error("接口触发 412 风控且重试失败: url=%s", url)
                raise BiliClientError(
                    "接口被风控拦截（412）。请确认 SESSDATA 为最新值，并尽量在常用网络环境下重试。"
                )

            if resp.status_code != 200:
                logger.error("接口返回非 200: url=%s status=%s", url, resp.status_code)
                raise BiliClientError(f"接口返回异常状态码：{resp.status_code}")

            try:
                payload = resp.json()
            except ValueError as exc:
                logger.exception("接口返回 JSON 解析失败: url=%s", url)
                raise BiliClientError("接口返回内容不是合法 JSON。") from exc

            return payload

        raise BiliClientError("请求失败，请稍后重试。")

    def validate_sessdata(self) -> None:
        """验证 Cookie 是否可用。"""
        payload = self._request("https://api.bilibili.com/x/web-interface/nav")
        if payload.get("code") == -101:
            raise InvalidSESSDATAError("SESSDATA 无效，请重新获取后再试。")
        if payload.get("code") != 0:
            msg = payload.get("message", "Cookie 校验失败。")
            raise BiliClientError(f"Cookie 校验失败：{msg}")

    def ensure_uid_exists(self, uid: str) -> None:
        """检查 UID 是否存在。"""
        payload = self._request(
            "https://api.bilibili.com/x/web-interface/card",
            params={"mid": uid},
        )
        if payload.get("code") != 0 or not payload.get("data", {}).get("card"):
            raise UIDNotFoundError("UID 不存在或无法访问该用户信息。")

    @staticmethod
    def _format_ts(ts: Any) -> str:
        """兼容 int/float/str 时间戳，解析失败时返回空字符串。"""
        try:
            ts_int = int(float(ts))
            if ts_int <= 0:
                return ""
            return datetime.fromtimestamp(ts_int).strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError, OSError, OverflowError):
            return ""

    @staticmethod
    def _safe_get(d: Dict[str, Any], keys: List[str], default: str = "") -> str:
        cur: Any = d
        for key in keys:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(key)
        if cur is None:
            return default
        return str(cur)

    def fetch_user_dynamics(self, uid: str, max_pages: int = 4) -> List[SpeechRecord]:
        """抓取用户空间动态作为“历史发言”来源之一。"""
        records: List[SpeechRecord] = []
        offset = ""

        for _ in range(max_pages):
            params = {"host_mid": uid}
            if offset:
                params["offset"] = offset

            payload = self._request(
                "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space",
                params=params,
            )

            if payload.get("code") != 0:
                raise BiliClientError(payload.get("message", "空间动态接口调用失败。"))

            data = payload.get("data", {})
            items = data.get("items", [])

            for item in items:
                modules = item.get("modules", {})
                desc_text = self._safe_get(modules, ["module_dynamic", "desc", "text"], "")
                major_archive_title = self._safe_get(
                    modules,
                    ["module_dynamic", "major", "archive", "title"],
                    "",
                )
                title = major_archive_title or desc_text[:30] or "空间动态"

                pub_ts = modules.get("module_author", {}).get("pub_ts", 0)
                jump_url = item.get("basic", {}).get("jump_url", "")
                if jump_url.startswith("//"):
                    jump_url = f"https:{jump_url}"

                if desc_text:
                    records.append(
                        SpeechRecord(
                            source_type="动态",
                            content=desc_text,
                            publish_time=self._format_ts(pub_ts) if pub_ts else "",
                            source_title=title,
                            source_url=jump_url,
                        )
                    )

            has_more = data.get("has_more", False)
            offset = data.get("offset", "")

            # 简单反爬：页与页之间随机停顿。
            time.sleep(random.uniform(0.5, 1.2))
            if not has_more:
                break

        return records

    def fetch_user_videos(self, uid: str, max_pages: int = 2) -> List[Dict[str, Any]]:
        """抓取用户投稿视频列表。"""
        videos: List[Dict[str, Any]] = []

        for pn in range(1, max_pages + 1):
            payload = self._request(
                "https://api.bilibili.com/x/space/arc/search",
                params={"mid": uid, "pn": pn, "ps": 20, "index": 1},
            )
            if payload.get("code") != 0:
                break

            vlist = payload.get("data", {}).get("list", {}).get("vlist", [])
            if not vlist:
                break

            for v in vlist:
                aid = v.get("aid")
                title = v.get("title", "")
                if aid:
                    videos.append({"aid": aid, "title": title})

            time.sleep(random.uniform(0.3, 0.8))

        return videos

    def fetch_comments_by_uid_on_video(
        self,
        target_uid: str,
        aid: int,
        video_title: str,
        max_pages: int = 3,
    ) -> List[SpeechRecord]:
        """在指定视频评论区中按 UID 过滤评论。"""
        records: List[SpeechRecord] = []
        next_cursor = 0

        for _ in range(max_pages):
            payload = self._request(
                "https://api.bilibili.com/x/v2/reply/main",
                params={
                    "type": 1,
                    "oid": aid,
                    "mode": 3,
                    "next": next_cursor,
                    "ps": 20,
                },
            )

            if payload.get("code") != 0:
                break

            data = payload.get("data", {})
            cursor = data.get("cursor", {})
            replies = data.get("replies") or []

            for reply in replies:
                member = reply.get("member", {})
                mid = str(member.get("mid", ""))
                if mid != str(target_uid):
                    continue

                ctime = int(reply.get("ctime", 0))
                content = reply.get("content", {}).get("message", "")
                rpid = reply.get("rpid", "")
                url = f"https://www.bilibili.com/video/av{aid}#reply{rpid}" if rpid else ""

                if content:
                    records.append(
                        SpeechRecord(
                            source_type="评论",
                            content=content,
                            publish_time=self._format_ts(ctime) if ctime else "",
                            source_title=video_title,
                            source_url=url,
                        )
                    )

            if not cursor.get("is_end", True):
                next_cursor = cursor.get("next", 0)
            else:
                break

            time.sleep(random.uniform(0.5, 1.0))

        return records

    def fetch_user_speeches(self, uid: str) -> List[SpeechRecord]:
        """抓取“历史发言”记录（动态 + 评论）。"""
        self.validate_sessdata()
        self.ensure_uid_exists(uid)

        all_records: List[SpeechRecord] = []

        # 1) 空间动态
        all_records.extend(self.fetch_user_dynamics(uid=uid, max_pages=4))

        # 2) 在其投稿视频评论区中筛选该 UID 的评论
        videos = self.fetch_user_videos(uid=uid, max_pages=2)
        for video in videos:
            all_records.extend(
                self.fetch_comments_by_uid_on_video(
                    target_uid=uid,
                    aid=int(video["aid"]),
                    video_title=video.get("title", ""),
                    max_pages=2,
                )
            )

        # 3) 去重（同一来源 + 同一内容 + 同一时间）
        unique: Dict[str, SpeechRecord] = {}
        for item in all_records:
            key = f"{item.source_type}|{item.publish_time}|{item.source_title}|{item.content}"
            unique[key] = item

        # 默认按时间倒序（字符串时间可直接比较：YYYY-MM-DD HH:MM:SS）
        result = sorted(unique.values(), key=lambda x: x.publish_time, reverse=True)
        return result
