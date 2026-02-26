"""
文字注入模組
將修飾後的文字注入到當前游標位置

使用剪貼簿 + Ctrl+V 方式，相容所有應用程式（Chrome、Firefox、桌面應用）
"""

import time
import logging

import pyperclip
import pyautogui

logger = logging.getLogger("VoiceType.Injector")

CLIPBOARD_SETTLE_SECONDS = 0.1


class TextInjector:
    """文字注入引擎"""

    def __init__(self, settings):
        self.settings = settings

    def inject(self, text: str):
        """將文字注入到當前游標位置（保護原有剪貼簿內容）"""
        if not text:
            return

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
