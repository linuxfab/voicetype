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
