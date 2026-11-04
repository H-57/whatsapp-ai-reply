from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTextEdit, QLabel, QMessageBox, QGroupBox)
from PySide6.QtCore import QThread, Signal, Slot
from browser.whatsapp_browser import WhatsAppBrowser
from storage.database import Database
from ai.reply_generator import ReplyGenerator
from ui.ai_settings_dialog import AISettingsDialog

class BrowserThread(QThread):
    contact_detected = Signal(str)
    messages_read = Signal(list)
    reply_generated = Signal(str)
    send_success = Signal()
    error_occurred = Signal(str)
    status_update = Signal(str)

    def __init__(self, profile_dir):
        super().__init__()
        self.profile_dir = profile_dir
        self.browser = WhatsAppBrowser(self.profile_dir)
        self.db = Database()
        self.ai = ReplyGenerator()
        self.running = True
        self.action_queue = []
        self.auto_reply_enabled = False

    def run(self):
        try:
            self.browser.start()
            self.status_update.emit("Browser started. Waiting for WhatsApp Web...")
        except Exception as e:
            self.error_occurred.emit(f"Failed to start browser: {e}")
            return

        import time
        last_poll_time = 0

        while self.running:
            if self.action_queue:
                action, data = self.action_queue.pop(0)
                try:
                    if action == "set_auto_reply":
                        self.auto_reply_enabled = data.get("enabled", False)
                        
                    elif action == "detect_chat":
                        contact = self.browser.get_current_contact()
                        if contact:
                            self.contact_detected.emit(contact)
                            msgs = self.browser.get_recent_messages(20)
                            
                            # Filter and record new incoming messages
                            for msg in msgs:
                                if msg["sender"] == "contact":
                                    if not self.db.is_message_processed(contact, msg["text"]):
                                        self.db.mark_message_processed(contact, msg["text"])
                                        
                            self.messages_read.emit(msgs)
                            self.status_update.emit(f"Detected chat: {contact}")
                        else:
                            self.error_occurred.emit("No active chat detected. Please open a contact.")
                    
                    elif action == "generate_reply":
                        msgs = data.get('messages', [])
                        self.status_update.emit("Generating AI reply...")
                        reply = self.ai.generate_reply(msgs)
                        self.reply_generated.emit(reply)
                        self.status_update.emit("Reply generated.")
                        
                    elif action == "send_message":
                        expected_contact = data.get('contact')
                        text = data.get('text')
                        self.status_update.emit("Sending message...")
                        self.browser.send_message(expected_contact, text)
                        self.db.mark_message_processed(expected_contact, text) # Also record outgoing
                        self.send_success.emit()
                        self.status_update.emit("Message sent successfully.")
                        
                except Exception as e:
                    self.error_occurred.emit(f"Action failed: {e}")
                    
            # Auto-reply polling loop
            if self.auto_reply_enabled and (time.time() - last_poll_time > 3):
                last_poll_time = time.time()
                try:
                    contact = self.browser.get_current_contact()
                    if contact:
                        msgs = self.browser.get_recent_messages(20)
                        if msgs:
                            last_msg = msgs[-1]
                            # Only act if the last message is from the contact (not us)
                            if last_msg["sender"] == "contact":
                                if not self.db.is_message_processed(contact, last_msg["text"]):
                                    self.status_update.emit(f"Auto-Reply: New message from {contact}")
                                    self.db.mark_message_processed(contact, last_msg["text"])
                                    
                                    # Update UI
                                    self.contact_detected.emit(contact)
                                    self.messages_read.emit(msgs)
                                    
                                    self.status_update.emit("Auto-Reply: Generating AI response...")
                                    reply = self.ai.generate_reply(msgs)
                                    self.reply_generated.emit(reply)
                                    
                                    self.status_update.emit("Auto-Reply: Sending message...")
                                    self.browser.send_message(contact, reply)
                                    self.db.mark_message_processed(contact, reply)
                                    
                                    self.status_update.emit("Auto-Reply: Message sent.")
                                    # Update UI with sent message
                                    self.messages_read.emit(msgs + [{"sender": "me", "text": reply}])
                except Exception as e:
                    print(f"Auto-reply loop error: {e}")
                    
            self.msleep(100)
            
        self.browser.stop()

    def queue_action(self, action, data=None):
        self.action_queue.append((action, data or {}))

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self, profile_dir):
        super().__init__()
        self.setWindowTitle("WhatsApp AI Reply")
        self.resize(600, 800)
        
        self.profile_dir = profile_dir
        self.db = Database()
        self.browser_thread = None
        self.current_contact = None
        self.current_messages = []
        
        self.init_ui()
        self.start_browser()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Status
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start (Detect Chat)")
        self.start_btn.clicked.connect(self.on_start_clicked)
        controls_layout.addWidget(self.start_btn)

        self.ai_config_btn = QPushButton("⚙️ AI Persona & Mini RAG")
        self.ai_config_btn.setStyleSheet("font-weight: bold;")
        self.ai_config_btn.clicked.connect(self.open_ai_settings)
        controls_layout.addWidget(self.ai_config_btn)
        
        layout.addLayout(controls_layout)

        # Chat info
        chat_group = QGroupBox("Current Chat")
        chat_layout = QVBoxLayout()
        self.contact_label = QLabel("Contact: None")
        chat_layout.addWidget(self.contact_label)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)
        chat_group.setLayout(chat_layout)
        layout.addWidget(chat_group)
        
        # AI Reply
        ai_group = QGroupBox("AI Suggested Reply")
        ai_layout = QVBoxLayout()
        
        from PySide6.QtWidgets import QCheckBox
        self.auto_reply_cb = QCheckBox("Enable Full Auto-Reply (Current Chat Only)")
        self.auto_reply_cb.stateChanged.connect(self.on_auto_reply_changed)
        ai_layout.addWidget(self.auto_reply_cb)
        
        self.reply_edit = QTextEdit()
        self.reply_edit.setEnabled(True)
        ai_layout.addWidget(self.reply_edit)
        
        btn_layout = QHBoxLayout()
        self.gen_btn = QPushButton("Generate Reply")
        self.gen_btn.clicked.connect(self.on_generate_clicked)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send_clicked)
        btn_layout.addWidget(self.gen_btn)
        btn_layout.addWidget(self.send_btn)
        ai_layout.addLayout(btn_layout)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

    def start_browser(self):
        self.browser_thread = BrowserThread(self.profile_dir)
        self.browser_thread.status_update.connect(self.update_status)
        self.browser_thread.error_occurred.connect(self.show_error)
        self.browser_thread.contact_detected.connect(self.update_contact)
        self.browser_thread.messages_read.connect(self.update_messages)
        self.browser_thread.reply_generated.connect(self.update_reply)
        self.browser_thread.send_success.connect(self.on_send_success)
        self.browser_thread.start()

    @Slot(str)
    def update_status(self, text):
        self.status_label.setText(text)

    @Slot(str)
    def show_error(self, text):
        QMessageBox.warning(self, "Error", text)
        self.status_label.setText("Error occurred.")

    @Slot(str)
    def update_contact(self, contact):
        self.current_contact = contact
        self.contact_label.setText(f"Contact: {contact}")

    @Slot(list)
    def update_messages(self, messages):
        self.current_messages = messages
        self.chat_display.clear()
        for msg in messages:
            sender = "Contact" if msg["sender"] == "contact" else "Me"
            text = msg["text"]
            self.chat_display.append(f"<b>{sender}:</b> {text}<br>")

    @Slot(str)
    def update_reply(self, reply):
        self.reply_edit.setText(reply)

    @Slot()
    def on_send_success(self):
        QMessageBox.information(self, "Success", "Message sent successfully!")
        self.reply_edit.clear()

    def on_start_clicked(self):
        if self.browser_thread:
            self.browser_thread.queue_action("detect_chat")

    def on_generate_clicked(self):
        if not self.current_messages:
            QMessageBox.warning(self, "Warning", "No messages found. Please click Start first.")
            return
        if self.browser_thread:
            self.browser_thread.queue_action("generate_reply", {"messages": self.current_messages})

    def on_send_clicked(self):
        text = self.reply_edit.toPlainText().strip()
        if not text or not self.current_contact:
            QMessageBox.warning(self, "Warning", "No contact selected or empty reply.")
            return
            
        reply = QMessageBox.question(self, 'Confirm Send', f"Send this message to {self.current_contact}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.browser_thread:
                self.browser_thread.queue_action("send_message", {
                    "contact": self.current_contact,
                    "text": text
                })

    def on_auto_reply_changed(self, state):
        is_checked = state != 0
        if self.browser_thread:
            self.browser_thread.queue_action("set_auto_reply", {"enabled": is_checked})
        
        if is_checked:
            self.status_label.setText("Auto-Reply ENABLED: Monitoring current chat...")
        else:
            self.status_label.setText("Auto-Reply DISABLED.")

    def open_ai_settings(self):
        dialog = AISettingsDialog(db=self.db, parent=self)
        dialog.exec()

    def closeEvent(self, event):
        if self.browser_thread:
            self.browser_thread.stop()
            self.browser_thread.wait()
        event.accept()
