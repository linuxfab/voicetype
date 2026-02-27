* 2026-02-27 12:03
* 重點: 新增 Gemini API 設定介面支援及錄音音效提示開關
* 影響: 
  1. 在 `ui/settings.html` 補上缺失的 `Gemini API Key` 欄位與相關 JavaScript 綁定。
  2. 修改 `config/settings.py`，新增 `playSounds` 選項，預設為 `True`。
  3. 修改 `main.py` 與 `ui/settings.html`，使錄音時的提示音效受 `playSounds` 設定控制，並於設定頁面的「進階設定」區塊提供開關。
* 結果: 使用者能在網頁設定中順利儲存 Gemini 金鑰作為本地或預設引擎使用；並且能自由決定是否開啟按下快捷鍵時的「嗶」聲回饋，提升客製化體驗。
* 更新者: antigravity agent

* 2026-02-27 12:00
* 重點: API 連線快取、縮短打字焦點延遲與強制繁中輸出
* 影響: 
  1. 在 `core/stt.py` 與 `core/llm.py` 中實作 `self._clients` 與 `self._session`，快取所有 API 用戶端，讓後續請求享有 Keep-Alive 連線池機制，避免重複 TLS 握手。
  2. 修改 `main.py` 與 `core/llm.py`，把按下快捷鍵時已取得的 `HWND` (前景視窗把柄) 向下傳遞至 LLM，避免在耗時的等待後呼叫同步 `psutil` 造成阻擋式延遲。
  3. 大幅縮減 `main.py` 的 `INJECT_DELAY_SECONDS` 至 `0.1` 並且導入迴圈頻繁輪詢焦點，最高可省下 200ms 的文字送出等待時間。
  4. 於 `core/llm.py` 中 `System Prompt` 強制掛載繁體中文 (zh-TW) 輸出指令，根除偶發性的簡體字產生。
* 結果: 顯著降低了每次語音觸發的網路 I/O 延遲，提升了打字輸出的極限順暢度與精確度。
* 更新者: antigravity agent

* 2026-02-27 09:03
* 重點: 更新 README.md 文件與文件規則
* 影響: 
  1. 將 `config.json` 的儲存路徑與設定方式補入 `README.md`。
  2. 在 `README.md` 開頭補上 GitHub 專案網址 (https://github.com/linuxfab/voicetype) 與最後更新時間。
  3. 在 LLM 引擎列表中新增 `Gemini 2.5 Flash Lite`，並標示為預設推薦選項。
* 結果: 文件更加完整，符合使用者閱讀習慣與專案規範。
* 更新者: antigravity agent

* 2026-02-27 08:35
* 重點: 新增 LLM 串流輸出 (Streaming) 支援功能
* 影響: 
  1. 修改 `config/settings.py` 的 Pydantic 模型，新增 `streamOutput` 設定項。
  2. 修改 `core/llm.py`，讓 OpenAI、Anthropic、Groq、Ollama 均能支援 Generator 串流模式返回文字。
  3. 修改 `core/injector.py` 與 `main.py`，如果是串流模式則使用 `keyboard.write()` 即時打字輸出，否則依然採用原來的剪貼簿方式。
* 結果: 在長段對話修飾時能感受到明顯的低延遲，並有著即時打字的視覺回饋，不需等待整個 LLM 處理結束。
* 更新者: antigravity agent

* 2026-02-27 08:25
* 重點: 導入 Pydantic 管理設定檔，並將開發環境切換至 uv
* 影響: 
  1. 將 `config/settings.py` 從 Dict 升級為基於 `pydantic` 與 `pydantic-settings`，實現自動型別檢查與更安全的預設值管理。
  2. 新增 `pydantic` 及 `pydantic-settings` 到 `requirements.txt` 中。
* 結果: 大幅提升程式碼的健壯性與後續擴展彈性。
* 更新者: antigravity agent

* 2026-02-27 07:54
* 重點: 新增更精準的語境偵測與中英夾雜 Regex 後處理
* 影響: 
  1. 修改 `requirements.txt` 以新增 `psutil` 與 `pywin32`。
  2. 修改 `core/llm.py`，使用 `win32gui` 和 `psutil` 取得執行檔名稱，更精確地給予 LLM 對應的 System Prompt 語氣。
  3. 修改 `core/llm.py`，增加 `re` 正則表達式，在 LLM 處理完後自動補上英文字母、數字與中文字元之間的半形空白，確保格式完全統一。
* 結果: 提昇 AI 語氣的準確度，並保證長效穩定的中英排版格式。
* 更新者: antigravity agent

* 2026-02-27 07:42
* 重點: 建立 `.env.example`
* 影響: 建立範例環境變數設定檔 `.env.example` 以供使用者參考
* 結果: 方便新使用者快速知道如何設定 API Key
* 更新者: antigravity agent

* 2026-02-27 07:37
* 重點: 增加剪貼簿保護、Esc 鍵取消錄音及 `.env` 支援
* 影響: 
  1. 修改 `core/injector.py`，注入剪貼簿前先備份內容，完成後還原。
  2. 修改 `core/hotkey.py` 及 `main.py`，新增 Esc 鍵來取消現有錄音。
  3. 修改 `config/settings.py`，現在允許讀取根目錄下的 `.env` 作為優先的 API 金鑰來源。
* 結果: 操作更加順暢，降低誤發與打字錯誤造成的風險；API 管理更符合開發慣例。
* 更新者: antigravity agent

* 2026-02-27 07:30
* 重點: 改用 uv 環境
* 影響: 替換原本的 python 及 pip 執行指令，更新 `start.bat`, `build.bat`, `build.py` 與 `README.md` 等檔案。
* 結果: 依賴安裝管理更加穩定、統一且獨立。
* 更新者: antigravity agent
