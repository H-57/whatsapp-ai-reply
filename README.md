# WhatsApp AI Reply 🤖💬

An intelligent desktop assistant and auto-reply tool for your **own WhatsApp Web account**.

Operates securely and locally via Playwright browser automation and Google Gemini AI. It only acts on the **currently open active conversation** — never scans your chat list, sends bulk messages, or performs unsolicited outreach.

---

## 🌟 Key Features

- **Safe by Design**: Operates strictly on whichever chat you manually open in WhatsApp Web.
- **Persistent Session**: Keeps your login session in `./whatsapp-profile` so you only scan the QR code once.
- **Contact Verification Guard**: Before sending any message, it cross-checks that the active conversation is still the intended recipient.
- **Smart Message Deduplication**: Uses a local SQLite database (`data/app.db`) to ensure the same message is never replied to repeatedly.
- **Flexible Modes**:
  - **Assisted Mode**: View recent messages, click *Generate Reply*, edit the suggested message in the UI, and click *Send*.
  - **Full Auto-Reply Mode**: Check *Enable Full Auto-Reply (Current Chat Only)* to let Gemini automatically reply in real-time to incoming messages in the open chat.
- **⚙️ Custom AI Persona & Prompt (GUI Popup)**: Configure custom instructions and behavior directly inside the app without touching any code. Stored permanently in SQLite DB.
- **📚 Built-in Mini RAG (Knowledge Base)**: Feed company details, pricing, FAQs, or any large reference text. The AI automatically retrieves the right chunks to answer questions accurately.
- **Modern AI Integration**: Powered by Google's latest `google-genai` SDK with configurable models (e.g., `gemini-1.5-flash`).

---

## 🖥️ Platform Compatibility

Works seamlessly across all major operating systems:
- 🐧 **Linux / Ubuntu** (Debian, Fedora, Arch, etc.)
- 🪟 **Windows** (10 / 11)
- 🍎 **macOS** (Intel & Apple Silicon M1/M2/M3/M4)

---

## 📋 Prerequisites

1. **Python 3.10+** installed:
   - Verify with: `python --version` or `python3 --version`
2. **Package Manager** (Choose one):
   - **Recommended:** [`uv`](https://docs.astral.sh/uv/) (Extremely fast, manages virtual environment automatically)
   - **Alternative:** Standard `pip` and Python `venv`
3. **Google Gemini API Key**:
   - Get a free API key from [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 Quick Setup & Installation

Navigate into the application folder:
```bash
cd whatsapp-ai-reply
```

### Option A: Using `uv` (Recommended)

1. **Install dependencies**:
   - **Linux / macOS**:
     ```bash
     uv pip install -r requirements.txt
     uv run playwright install chromium
     ```
   - **Windows** (PowerShell or Command Prompt):
     ```powershell
     uv pip install -r requirements.txt
     uv run playwright install chromium
     ```

2. **On Linux (Ubuntu/Debian only)**:
   If Chromium dependencies are missing on your Linux distribution, install system libraries:
   ```bash
   uv run playwright install-deps chromium
   ```

---

### Option B: Using Standard Python `venv` & `pip`

1. **Create and activate virtual environment**:
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows** (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Windows** (Command Prompt):
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate.bat
     ```

2. **Install requirements & Playwright browser**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

   *(On Linux/Ubuntu only, if required: `playwright install-deps chromium`)*

---

## ⚙️ Configuration

1. Create your `.env` configuration file from the template:
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```
   - **Windows** (PowerShell):
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Windows** (CMD):
     ```cmd
     copy .env.example .env
     ```

2. Open `.env` in any text editor and fill in your Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```

---

## 🎬 How to Run

From inside the `whatsapp-ai-reply` directory:

- **Using `uv`**:
  ```bash
  uv run python app.py
  ```

- **Using standard Python (with virtualenv activated)**:
  ```bash
  python app.py
  ```

---

## 📖 Usage Guide

### 1. First-Time Launch (QR Code Scan)
- The app will launch a visible Chromium browser window loading WhatsApp Web.
- Open WhatsApp on your phone (`Settings` > `Linked Devices` > `Link a Device`) and scan the QR code displayed in Chromium.
- *Your login session is securely saved in `./whatsapp-profile/` on your computer, so you won't need to scan it again on future launches.*

### 2. Manual Assisted Mode
1. In the WhatsApp Web window, click and open the contact/chat you want to interact with.
2. In the WhatsApp AI Reply application window, click **"Start (Detect Chat)"**.
3. The app detects the open contact name and loads recent messages.
4. Click **"Generate Reply"** to get a suggestion from Gemini AI.
5. Review or edit the suggested message in the text box.
6. Click **"Send"** to send the message.

### 3. Full Auto-Reply Mode
1. Open the specific contact/chat in WhatsApp Web.
2. In the application window, check **"Enable Full Auto-Reply (Current Chat Only)"**.
3. The application will monitor the active chat:
   - When a new incoming message arrives from the contact, it checks the local database to verify it's new.
   - Automatically asks Gemini AI for a natural response.
   - Types and sends the reply without requiring manual confirmation.
4. To stop automation at any time, simply uncheck the box.

---

## 📂 Project Structure

```text
whatsapp-ai-reply/
├── app.py                     # Desktop application entry point
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Files excluded from version control
├── README.md                  # Complete documentation
│
├── browser/                   # Playwright browser controller
│   ├── selectors.py           # WhatsApp Web DOM selectors
│   └── whatsapp_browser.py    # Chromium session & chat interaction
│
├── ai/                        # AI processing module
│   └── reply_generator.py     # Google GenAI (Gemini) client
│
├── storage/                   # Local database storage
│   └── database.py            # SQLite deduplication storage
│
├── ui/                        # Desktop User Interface
│   └── main_window.py         # PySide6 desktop window & background thread
│
├── data/
│   └── app.db                 # Processed message history (auto-created)
│
└── whatsapp-profile/          # Saved browser profile (auto-created)
```

---

## 🔒 Security & Privacy

- **No Credential Theft**: WhatsApp credentials and tokens remain entirely inside Chromium's local profile (`whatsapp-profile/`).
- **No Unsolicited Messages**: The bot is architected specifically to ignore all other chats and only operate on the single chat you open on your screen.
- **Git Safety**: Both `.env` (API keys), `whatsapp-profile/` (browser session), and `app.db` (message hashes) are added to `.gitignore` to prevent sensitive data leaks.

---

## 🛠️ Troubleshooting

- **No active chat detected**:
  - Make sure you actually clicked on a chat so that the contact header is visible on the right-hand panel of WhatsApp Web.
- **AI generation error**:
  - Verify that `GEMINI_API_KEY` in `.env` is valid and has active quota.
- **Linux display issues (X11 / Wayland)**:
  - If PySide6 fails to create a window on headless or Wayland servers, set:
    ```bash
    export QT_QPA_PLATFORM=xcb
    ```
- **Playwright executable error**:
  - Run `playwright install chromium` (or `uv run playwright install chromium`).
