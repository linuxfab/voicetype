"""
文字注入模組
將修飾後的文字注入到當前游標位置

使用剪貼簿 + Ctrl+V 方式，相容所有應用程式（Chrome、Firefox、桌面應用）
支援串流打字 (streaming) 注入
"""

import time
import logging
from typing import Generator, Union

import pyperclip
import pyautogui
import keyboard

logger = logging.getLogger("VoiceType.Injector")

CLIPBOARD_SETTLE_SECONDS = 0.1
STREAM_TYPING_DELAY = 0.005  # 模擬打字的延遲


class TextInjector:
    """文字注入引擎"""

    def __init__(self, settings):
        self.settings = settings

    def inject(self, text_or_generator: Union[str, Generator[str, None, None]]):
        """
        注入文字或串流文字到當前游標位置
        """
        if isinstance(text_or_generator, str):
            if not text_or_generator:
                return
            self._inject_clipboard(text_or_generator)
        else:
            self._inject_stream(text_or_generator)

    def _inject_clipboard(self, text: str):
        """將文字注入到當前游標位置（保護原有剪貼簿內容）"""
        try:
            # 1. 備份原有剪貼簿內容
            original_clipboard = pyperclip.paste()
            
            # 2. 寫入新文字並貼上
            pyperclip.copy(text)
            time.sleep(CLIPBOARD_SETTLE_SECONDS)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(CLIPBOARD_SETTLE_SECONDS)
            
            # 3. 還原剪貼簿內容
            pyperclip.copy(original_clipboard)
            
            logger.info("Injected %d characters via clipboard (and restored original content)", len(text))
        except Exception as e:
            logger.error("Text injection failed: %s", e)
            raise

    def _inject_stream(self, generator: Generator[str, None, None]):
        """串流打字注入（模擬鍵盤逐字輸入）"""
        try:
            count = 0
            for chunk in generator:
                if chunk:
                    # 使用 keyboard.write 來輸出，因為它支援 Unicode
                    keyboard.write(chunk, delay=STREAM_TYPING_DELAY)
                    count += len(chunk)
            logger.info("Stream injected %d characters", count)
        except Exception as e:
            logger.error("Stream injection failed: %s", e)
            raise
