"""
LLM 智能修飾模組
將 STT 原始文字送給 LLM 進行去贅字、修正、格式化
支援 OpenAI ChatGPT、Anthropic Claude、Groq、Ollama
"""

import logging
import re
from typing import Generator, Union

from config.settings import DEFAULT_SYSTEM_PROMPT

logger = logging.getLogger("VoiceType.LLM")


def _format_mixed_text(text: str) -> str:
    """中英夾雜自動加空格 Regex 後處理"""
    # 英文/數字後面接著中文字
    text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fa5])', r'\1 \2', text)
    # 中文字後面接著英文/數字
    text = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9])', r'\1 \2', text)
    return text


class LLMProcessor:
    """LLM 文字修飾引擎"""

    def __init__(self, settings):
        self.settings = settings
        self._clients = {}
        self._session = None

    def polish(self, raw_text: str, process_hwnd=None) -> Union[str, Generator[str, None, None]]:
        """將 STT 原始文字修飾為乾淨的輸出 (可能是字串，或字串生成器)"""
        cfg = self.settings.get_config()
        provider = cfg.get("llmProvider", "openai")
        stream = cfg.get("streamOutput", False)

        # 如果文字很短且乾淨，可以跳過 LLM
        if len(raw_text.strip()) < 3:
            if stream:
                def _short_gen():
                    yield raw_text.strip()
                return _short_gen()
            else:
                return raw_text.strip()

        try:
            if provider == "openai":
                result = self._polish_openai(raw_text, cfg, stream, process_hwnd)
            elif provider == "anthropic":
                result = self._polish_anthropic(raw_text, cfg, stream, process_hwnd)
            elif provider == "groq":
                result = self._polish_groq(raw_text, cfg, stream, process_hwnd)
            elif provider == "ollama":
                result = self._polish_ollama(raw_text, cfg, stream, process_hwnd)
            elif provider == "gemini":
                result = self._polish_gemini(raw_text, cfg, stream, process_hwnd)
            else:
                logger.warning("未知 LLM 引擎 %s，直接輸出原文", provider)
                result = [raw_text.strip()] if stream else raw_text.strip()

            if stream:
                return self._stream_generator_wrapper(result, cfg)
            else:
                # Regex 後處理確保中英夾雜排版一致 (僅非串流模式支援)
                if cfg.get("autoFormat", True) and isinstance(result, str):
                    result = _format_mixed_text(result)
                return result

        except Exception as e:
            logger.error("LLM 修飾失敗: %s，回退為原文", e)
            if stream:
                def _error_gen():
                    yield raw_text.strip()
                return _error_gen()
            return raw_text.strip()

    def _stream_generator_wrapper(self, generator, cfg):
        """包裝原始的 generator，以符合返回類型 (串流模式下暫無法輕易做到完整 Regex)"""
        for chunk in generator:
            if chunk:
                yield chunk

    def _get_system_prompt(self, cfg: dict, process_hwnd=None) -> str:
        """取得系統提示詞（含語境資訊）"""
        base_prompt = cfg.get("systemPrompt", DEFAULT_SYSTEM_PROMPT)

        if cfg.get("contextAware", True):
            context = self._detect_context(process_hwnd)
            if context:
                base_prompt += f"\n\n當前語境：{context}"

        base_prompt += "\n\n重要規則：請一律使用繁體中文 (Traditional Chinese, zh-TW) 輸出，絕對不要輸出簡體字。"
        return base_prompt

    def _detect_context(self, process_hwnd=None) -> str:
        """偵測當前使用的 App 來調整語氣"""
        try:
            import win32gui
            import win32process
            import psutil
            
            hwnd = process_hwnd if process_hwnd else win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd).lower()
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                exe_name = process.name().lower()
            except Exception:
                exe_name = ""

            if exe_name in ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "arc.exe"]:
                if any(k in title for k in ["gmail", "outlook", "mail"]):
                    return "用戶正在瀏覽器中撰寫郵件，語氣應正式專業"
                elif any(k in title for k in ["chat", "messenger", "line", "discord"]):
                    return "用戶正在網頁版通訊軟體聊天，語氣可以輕鬆口語"
                else:
                    return "用戶在瀏覽網頁，可能在填寫表單或撰筆記，語氣應清晰有理"

            elif exe_name in ["code.exe", "pycharm.exe", "idea.exe", "devenv.exe", "cursor.exe", "windows terminal.exe", "powershell.exe", "cmd.exe"]:
                return "用戶在寫程式，可能是在寫註解、撰寫技術文件或 Commit Message，語氣應技術性且簡潔"

            elif exe_name in ["winword.exe", "excel.exe", "powerpnt.exe", "obsidian.exe", "notion.exe", "evernote.exe"]:
                return "用戶在撰寫文件或筆記，語氣應清晰有條理"

            elif exe_name in ["discord.exe", "line.exe", "slack.exe", "teams.exe", "telegram.exe", "whatsapp.exe"]:
                if exe_name in ["slack.exe", "teams.exe"]:
                    return "用戶在工作通訊軟體，語氣應簡潔專業"
                return "用戶正在通訊軟體聊天，語氣可以輕鬆口語"
                
            if any(k in title for k in ["outlook", "gmail", "mail", "thunderbird"]):
                return "用戶正在撰寫郵件，語氣應正式專業"
            elif any(k in title for k in ["word", "docs", "notion", "obsidian"]):
                return "用戶在撰寫文件，語氣應清晰有條理"

        except ImportError:
            logger.debug("win32gui / psutil not installed, context detection disabled.")
        except Exception as e:
            logger.debug("Context detection failed: %s", e)
            
        return ""

    # ── OpenAI ChatGPT ───────────────────────────────────────────────────────

    def _polish_openai(self, raw_text: str, cfg: dict, stream: bool, process_hwnd=None):
        from openai import OpenAI

        api_key = self.settings.get_api_key("openai")
        if not api_key:
            raise ValueError("OpenAI API Key 未設定")

        if "openai" not in self._clients:
            self._clients["openai"] = OpenAI(api_key=api_key)
        client = self._clients["openai"]
        
        model = cfg.get("llmModel", "gpt-4o-mini")
        system_prompt = self._get_system_prompt(cfg, process_hwnd)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.3,
            max_tokens=2048,
            stream=stream,
        )

        if stream:
            def _gen(keepalive_client, resp):
                for chunk in resp:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
            return _gen(client, response)
        else:
            return response.choices[0].message.content.strip()

    # ── Anthropic Claude ─────────────────────────────────────────────────────

    def _polish_anthropic(self, raw_text: str, cfg: dict, stream: bool, process_hwnd=None):
        import anthropic

        api_key = self.settings.get_api_key("anthropic")
        if not api_key:
            raise ValueError("Anthropic API Key 未設定")

        if "anthropic" not in self._clients:
            self._clients["anthropic"] = anthropic.Anthropic(api_key=api_key)
        client = self._clients["anthropic"]
        
        model = cfg.get("llmModel", "claude-haiku-4-5-20251001")
        system_prompt = self._get_system_prompt(cfg, process_hwnd)

        if stream:
            response = client.messages.stream(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": raw_text},
                ],
            )
            def _gen(keepalive_client, stream_resp):
                with stream_resp as stream_manager:
                    for text_event in stream_manager.text_stream:
                        yield text_event
            return _gen(client, response)
        else:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": raw_text},
                ],
            )
            return response.content[0].text.strip()

    # ── Groq（OpenAI 相容）───────────────────────────────────────────────────

    def _polish_groq(self, raw_text: str, cfg: dict, stream: bool, process_hwnd=None):
        from openai import OpenAI

        api_key = self.settings.get_api_key("groq")
        if not api_key:
            raise ValueError("Groq API Key 未設定")

        if "groq" not in self._clients:
            self._clients["groq"] = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
            )
        client = self._clients["groq"]
        
        model = cfg.get("llmModel", "llama-3.3-70b-versatile")
        system_prompt = self._get_system_prompt(cfg, process_hwnd)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.3,
            max_tokens=2048,
            stream=stream,
        )

        if stream:
            def _gen(keepalive_client, resp):
                for chunk in resp:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
            return _gen(client, response)
        else:
            return response.choices[0].message.content.strip()

    # ── Ollama 本地 ──────────────────────────────────────────────────────────

    def _polish_ollama(self, raw_text: str, cfg: dict, stream: bool, process_hwnd=None):
        import requests
        import json

        endpoint = self.settings.get_api_key("ollama") or "http://localhost:11434"
        model = cfg.get("llmModel", "qwen3:8b")
        system_prompt = self._get_system_prompt(cfg, process_hwnd)
        
        if self._session is None:
            self._session = requests.Session()

        response = self._session.post(
            f"{endpoint}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text},
                ],
                "stream": stream,
                "options": {"temperature": 0.3},
            },
            stream=stream,
            timeout=30 if not stream else None,
        )
        response.raise_for_status()

        if stream:
            def _gen():
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        yield data["message"]["content"]
            return _gen()
        else:
            data = response.json()
            return data["message"]["content"].strip()

    # ── Gemini (Google GenAI) ────────────────────────────────────────────────

    def _polish_gemini(self, raw_text: str, cfg: dict, stream: bool, process_hwnd=None):
        from google import genai
        from google.genai import types

        api_key = self.settings.get_api_key("gemini")
        if not api_key:
            raise ValueError("Gemini API Key 未設定")

        if "gemini" not in self._clients:
            self._clients["gemini"] = genai.Client(api_key=api_key)
        client = self._clients["gemini"]
        
        model = cfg.get("llmModel", "gemini-2.5-flash-lite")
        system_prompt = self._get_system_prompt(cfg, process_hwnd)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=2048,
        )

        if stream:
            response_stream = client.models.generate_content_stream(
                model=model,
                contents=raw_text,
                config=config,
            )
            def _gen(keepalive_client, resp):
                for chunk in resp:
                    if chunk.text:
                        yield chunk.text
            return _gen(client, response_stream)
        else:
            response = client.models.generate_content(
                model=model,
                contents=raw_text,
                config=config,
            )
            return response.text.strip() if response.text else ""
