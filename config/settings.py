import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("VoiceType.Settings")


class ApiKeys(BaseModel):
    groq: str = ""
    openai: str = ""
    anthropic: str = ""
    gemini: str = ""
    ollama: str = "http://localhost:11434"


class VoiceTypeConfig(PydanticBaseSettings):
    """應用程式設定的 Pydantic 模型"""
    sttProvider: Literal["groq", "openai", "local"] = "groq"
    llmProvider: Literal["openai", "anthropic", "groq", "ollama", "gemini"] = "openai"
    sttModel: str = "whisper-large-v3-turbo"
    llmModel: str = "gpt-4o-mini"
    apiKeys: ApiKeys = Field(default_factory=ApiKeys)
    hotkey: Literal["RightAlt", "RightCtrl", "F9", "CapsLock", "ScrollLock"] = "RightAlt"
    language: Literal["auto", "zh-TW", "zh-CN", "en", "ja"] = "auto"
    outputMode: str = "clipboard"
    streamOutput: bool = False
    removeFiller: bool = True
    autoFormat: bool = True
    contextAware: bool = True
    dictionary: List[str] = Field(default_factory=list)
    systemPrompt: str = (
        "你是一個語音轉文字的智能編輯器。請對用戶的口述內容進行以下處理：\n"
        "1. 移除口頭禪和贅字（嗯、啊、那個、就是說、然後、對...）\n"
        "2. 如果用戶在中途自我更正，只保留最終意圖\n"
        "3. 加入適當的標點符號和段落\n"
        "4. 保持用戶原意，不要增添內容\n"
        "5. 如果是列表或步驟，自動格式化\n"
        "6. 保持用戶說話的語言輸出。如果用戶說中文，一律使用繁體中文（不可輸出簡體）。如果用戶說英文，則輸出英文。\n"
        "7. 中英夾雜處理規則：\n"
        "   - 英文單字前後加一個半形空格與中文隔開（例：使用 Python 開發）\n"
        "   - 英文專有名詞保持正確大小寫（例：GitHub、macOS、JavaScript、API、iPhone）\n"
        "   - 語音辨識常見錯誤修正：把拼音化的英文還原（例：「皮爾森」→ Python、「歐批艾」→ API）\n"
        "   - 英文縮寫用全大寫（例：API、URL、HTML、CSS、SDK）\n\n"
        "只回覆修正後的文字，不要任何解釋、前綴或引號。"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # 允許來自環境變數的覆寫，但不強求所有設定都在 .env 裡面
        extra="ignore"
    )


# 匯出預設系統提示詞，供 llm.py 等模組使用，因為 Pydantic 在實例化前我們需要預設字串
DEFAULT_SYSTEM_PROMPT = VoiceTypeConfig.model_fields["systemPrompt"].default


class Settings:
    """設定管理器 (與舊版相容的封裝)"""

    def __init__(self, config_dir: Path | None = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            if os.name == "nt":
                base = os.environ.get("APPDATA", os.path.expanduser("~"))
            else:
                base = os.path.expanduser("~/.config")
            self.config_dir = Path(base) / "voicetype"

        self.config_path = self.config_dir / "config.json"
        self._config_model: VoiceTypeConfig | None = None

    def load(self) -> dict:
        """載入設定檔，不存在則建立預設設定"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                
                # Pydantic 自動處理合併與預設值
                self._config_model = VoiceTypeConfig(**saved)
                logger.info("設定已載入: %s", self.config_path)
            except Exception as e:
                logger.error("設定檔讀取或驗證失敗: %s，使用預設值", e)
                self._config_model = VoiceTypeConfig()
        else:
            logger.info("設定檔不存在，建立預設設定...")
            self._config_model = VoiceTypeConfig()
            self.save()

        return self._config_model.model_dump()

    def save(self):
        """儲存設定到檔案 (將 Pydantic Model 轉回 Dict 儲存)"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self._config_model:
            self._config_model = VoiceTypeConfig()

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config_model.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info("設定已儲存: %s", self.config_path)

    def get_config(self) -> dict:
        """取得當前設定（若未載入則自動載入）"""
        if not self._config_model:
            self.load()
        return self._config_model.model_dump()

    def update(self, key: str, value):
        """更新單一設定值"""
        if not self._config_model:
            self.load()
        
        # 建立一個新的 dict 再重新實例化，依靠 Pydantic 做型別檢查
        current = self._config_model.model_dump()
        current[key] = value
        
        try:
            self._config_model = VoiceTypeConfig(**current)
            self.save()
        except Exception as e:
            logger.error("設定值無效: %s", e)
            raise ValueError(f"設定值無效: {e}")

    def update_all(self, new_config: dict):
        """批次更新設定"""
        if not self._config_model:
            self.load()
        
        current = self._config_model.model_dump()
        # 遞迴更新 apiKeys 等字典
        if "apiKeys" in new_config and "apiKeys" in current:
            current["apiKeys"].update(new_config["apiKeys"])
            del new_config["apiKeys"]
            
        current.update(new_config)
        
        try:
            self._config_model = VoiceTypeConfig(**current)
            self.save()
        except Exception as e:
            logger.error("更新設定失敗: %s", e)
            raise ValueError(f"更新設定失敗: {e}")

    def get_api_key(self, provider: str) -> str:
        """取得指定引擎的 API Key (優先讀取 .env 或環境變數)"""
        # Pydantic BaseSettings 不會自動幫深層 (Nested) model 取聯集環境變數
        # 所以維持這裡手動讀 ENV 的邏輯，如果使用者有設 OPENAI_API_KEY，優先用。
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "ollama": "OLLAMA_API_BASE"
        }
        
        env_var_name = env_keys.get(provider)
        if env_var_name:
            env_val = os.environ.get(env_var_name)
            if env_val:
                return env_val

        # 若 .env 或環境變數中沒有，則讀取 model 中的設定
        if not self._config_model:
            self.load()
        keys_dict = self._config_model.apiKeys.model_dump()
        return keys_dict.get(provider, "")

    def set_api_key(self, provider: str, key: str):
        """設定 API Key (僅寫入 config.json)"""
        if not self._config_model:
            self.load()
            
        current_keys = self._config_model.apiKeys.model_dump()
        current_keys[provider] = key
        
        current_config = self._config_model.model_dump()
        current_config["apiKeys"] = current_keys
        
        try:
            self._config_model = VoiceTypeConfig(**current_config)
            self.save()
        except Exception as e:
            logger.error("更新 API Key 失敗: %s", e)

    def validate(self) -> list[str]:
        """驗證設定值，回傳警告訊息列表 (因 Pydantic 會自動阻擋無效值，此處基本上只會空陣列)"""
        warnings = []
        if not self._config_model:
            return warnings
            
        cfg = self.get_config()
        # 原有的 VALID_STT_PROVIDERS 等等，現在透過 Literal 已經保護了
        # 此處保留做為向後相容
        valid_stt = ["groq", "openai", "local"]
        valid_llm = ["openai", "anthropic", "groq", "ollama"]
        valid_hotkeys = ["RightAlt", "RightCtrl", "F9", "CapsLock", "ScrollLock"]
        valid_lang = ["auto", "zh-TW", "zh-CN", "en", "ja"]
        
        if cfg.get("sttProvider") not in valid_stt:
            warnings.append(f"Invalid STT provider: {cfg.get('sttProvider')}")
        if cfg.get("llmProvider") not in valid_llm:
            warnings.append(f"Invalid LLM provider: {cfg.get('llmProvider')}")
        if cfg.get("hotkey") not in valid_hotkeys:
            warnings.append(f"Invalid hotkey: {cfg.get('hotkey')}")
        if cfg.get("language") not in valid_lang:
            warnings.append(f"Invalid language: {cfg.get('language')}")
            
        return warnings
