"""
全域快捷鍵管理模組
監聽 Push-to-Talk 快捷鍵（按住說話，放開處理）
支援 Esc 鍵取消錄音
"""

import logging
import keyboard

logger = logging.getLogger("VoiceType.Hotkey")

# 快捷鍵名稱映射到 keyboard 模組的鍵名
HOTKEY_MAP = {
    "RightAlt": "right alt",
    "RightCtrl": "right ctrl",
    "F9": "f9",
    "CapsLock": "caps lock",
    "ScrollLock": "scroll lock",
}


class HotkeyManager:
    """全域快捷鍵管理器"""

    def __init__(self, settings):
        self.settings = settings
        self._on_press = None
        self._on_release = None
        self._on_cancel = None
        self._running = False
        self._hotkey_name = None
        self._press_hook = None
        self._release_hook = None
        self._cancel_hook = None

    def register(self, on_press, on_release, on_cancel=None):
        """
        註冊 Push-to-Talk 快捷鍵

        Args:
            on_press: 按下 PTT 鍵時的回呼函式
            on_release: 釋放 PTT 鍵時的回呼函式
            on_cancel: 按下 Esc 鍵取消錄音的回呼函式
        """
        self._on_press = on_press
        self._on_release = on_release
        self._on_cancel = on_cancel
        self._running = True

        cfg = self.settings.get_config()
        hotkey_id = cfg.get("hotkey", "RightAlt")
        key_name = HOTKEY_MAP.get(hotkey_id, "right alt")
        self._hotkey_name = key_name

        # 註冊按下和釋放事件，suppress=True 阻止快捷鍵穿透到目標應用
        self._press_hook = keyboard.on_press_key(key_name, self._handle_press, suppress=True)
        self._release_hook = keyboard.on_release_key(key_name, self._handle_release, suppress=True)
        
        # 註冊 Esc 作為取消錄音鍵 (不阻擋一般 Esc 功能，僅在錄音時有作用)
        self._cancel_hook = keyboard.on_press_key("esc", self._handle_cancel, suppress=False)

        logger.info("Hotkey registered: %s -> %s (Esc to cancel)", hotkey_id, key_name)

    def _handle_press(self, event):
        """處理按下事件"""
        if self._running and self._on_press:
            try:
                self._on_press()
            except Exception as e:
                logger.error("Hotkey press callback error: %s", e)

    def _handle_release(self, event):
        """處理釋放事件"""
        if self._running and self._on_release:
            try:
                self._on_release()
            except Exception as e:
                logger.error("Hotkey release callback error: %s", e)

    def _handle_cancel(self, event):
        """處理取消 (Esc) 事件"""
        if self._running and self._on_cancel:
            try:
                self._on_cancel()
            except Exception as e:
                logger.error("Hotkey cancel callback error: %s", e)

    def unhook(self):
        """移除此管理器註冊的 hook（不影響其他程式的 hook）"""
        if self._press_hook:
            try:
                keyboard.unhook(self._press_hook)
            except Exception:
                pass
            self._press_hook = None
            
        if self._release_hook:
            try:
                keyboard.unhook(self._release_hook)
            except Exception:
                pass
            self._release_hook = None
            
        if self._cancel_hook:
            try:
                keyboard.unhook(self._cancel_hook)
            except Exception:
                pass
            self._cancel_hook = None

    def stop(self):
        """停止快捷鍵監聽"""
        self._running = False
        self.unhook()
        logger.info("Hotkey listener stopped")
