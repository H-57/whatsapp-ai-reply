from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QMessageBox, QTabWidget, QWidget, QFileDialog
)
from PySide6.QtCore import Qt
from storage.database import Database
from ai.default_prompt import DEFAULT_SYSTEM_PROMPT

class AISettingsDialog(QDialog):
    """
    Popup dialog allowing the user to configure:
    1. Custom System Prompt / Behavior instructions (saved in SQLite DB)
    2. Mini RAG Knowledge Base / Huge Info Text (saved in SQLite DB)
    """
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("AI Configuration & Mini RAG Knowledge Base")
        self.resize(700, 580)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # --- TAB 1: System Prompt / Behavior ---
        prompt_tab = QWidget()
        prompt_layout = QVBoxLayout(prompt_tab)

        prompt_desc = QLabel(
            "<b>AI Persona & Behavior Prompt:</b><br>"
            "Define how the AI should talk, what personality to take, how to reply, language, emojis, etc.<br>"
            "<i>(Changes are automatically saved to your local database)</i>"
        )
        prompt_desc.setWordWrap(True)
        prompt_layout.addWidget(prompt_desc)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your custom system prompt here...")
        prompt_layout.addWidget(self.prompt_edit)

        prompt_btn_row = QHBoxLayout()
        reset_prompt_btn = QPushButton("Reset to Default Prompt")
        reset_prompt_btn.clicked.connect(self.on_reset_prompt)
        prompt_btn_row.addWidget(reset_prompt_btn)
        prompt_btn_row.addStretch()
        prompt_layout.addLayout(prompt_btn_row)

        tabs.addTab(prompt_tab, "🤖 AI Persona & Behavior")

        # --- TAB 2: Mini RAG Knowledge Base ---
        rag_tab = QWidget()
        rag_layout = QVBoxLayout(rag_tab)

        rag_desc = QLabel(
            "<b>Mini RAG Knowledge Base (Information & Q&A Context):</b><br>"
            "Paste product details, pricing, FAQs, your bio, company info, or any large text here.<br>"
            "When someone asks questions, the AI will automatically retrieve relevant pieces from this text to answer accurately."
        )
        rag_desc.setWordWrap(True)
        rag_layout.addWidget(rag_desc)

        self.rag_edit = QTextEdit()
        self.rag_edit.setPlaceholderText(
            "Paste your knowledge base here...\n\n"
            "Example:\n"
            "- Business: TechCraft Solutions\n"
            "- Services: Web Development ($500), Mobile Apps ($1000)\n"
            "- Working Hours: 9 AM to 6 PM IST\n"
            "- Address: Sector 21, Gurugram, India\n"
            "- Refund policy: 14 days full refund..."
        )
        rag_layout.addWidget(self.rag_edit)

        rag_btn_row = QHBoxLayout()
        import_file_btn = QPushButton("📁 Import from .txt / .md File")
        import_file_btn.clicked.connect(self.on_import_file)
        clear_rag_btn = QPushButton("Clear Knowledge")
        clear_rag_btn.clicked.connect(self.on_clear_rag)
        rag_btn_row.addWidget(import_file_btn)
        rag_btn_row.addWidget(clear_rag_btn)
        rag_btn_row.addStretch()
        rag_layout.addLayout(rag_btn_row)

        tabs.addTab(rag_tab, "📚 Mini RAG (Huge Info / Knowledge)")

        main_layout.addWidget(tabs)

        # --- Bottom Action Buttons ---
        bottom_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save & Apply")
        self.save_btn.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.save_btn.clicked.connect(self.on_save)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.cancel_btn)
        bottom_layout.addWidget(self.save_btn)
        main_layout.addLayout(bottom_layout)

    def load_settings(self):
        saved_prompt = self.db.get_setting("system_prompt", DEFAULT_SYSTEM_PROMPT)
        self.prompt_edit.setText(saved_prompt)

        kb_entries = self.db.get_knowledge_base()
        if kb_entries:
            combined_content = "\n\n".join([entry[2] for entry in kb_entries])
            self.rag_edit.setText(combined_content)

    def on_reset_prompt(self):
        reply = QMessageBox.question(
            self, "Reset Prompt", "Reset prompt to the default conversation-continuity prompt?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.prompt_edit.setText(DEFAULT_SYSTEM_PROMPT)

    def on_clear_rag(self):
        self.rag_edit.clear()

    def on_import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Text or Markdown file", "", "Text Files (*.txt *.md *.csv);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                current_text = self.rag_edit.toPlainText().strip()
                if current_text:
                    self.rag_edit.setPlainText(current_text + "\n\n" + content)
                else:
                    self.rag_edit.setPlainText(content)
                QMessageBox.information(self, "Imported", f"Successfully imported {len(content)} characters!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to read file: {e}")

    def on_save(self):
        prompt_text = self.prompt_edit.toPlainText().strip()
        rag_text = self.rag_edit.toPlainText().strip()

        if not prompt_text:
            prompt_text = DEFAULT_SYSTEM_PROMPT

        # Save prompt to DB
        self.db.set_setting("system_prompt", prompt_text)

        # Save RAG Knowledge Base to DB
        self.db.set_knowledge_base(rag_text)

        QMessageBox.information(self, "Success", "AI Prompt & Mini RAG Knowledge Base saved successfully!")
        self.accept()
