from playwright.sync_api import sync_playwright
from .selectors import MAIN_PANE, CONTACT_NAME, MESSAGE_ROW, MESSAGE_IN_CLASS, MESSAGE_OUT_CLASS, MESSAGE_TEXT

class WhatsAppBrowser:
    def __init__(self, profile_dir):
        self.profile_dir = profile_dir
        self.playwright = None
        self.context = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        # Launch Chromium visibly, using persistent context
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 720}
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto("https://web.whatsapp.com")

    def stop(self):
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def get_current_contact(self):
        try:
            # Check if main pane is visible
            if not self.page.is_visible(MAIN_PANE):
                return None
            
            # Get contact name
            header = self.page.locator(MAIN_PANE).locator("header")
            if not header.is_visible():
                return None
                
            contact_el = header.locator(CONTACT_NAME).first
            if contact_el.is_visible():
                return contact_el.inner_text()
            return None
        except Exception as e:
            print(f"Error getting contact: {e}")
            return None

    def get_recent_messages(self, limit=20):
        messages = []
        try:
            if not self.page.is_visible(MAIN_PANE):
                return messages

            # Get the current contact name for comparison
            current_contact = self.get_current_contact()
            if not current_contact:
                current_contact = ""

            # Get all message rows in the current chat
            message_nodes = self.page.locator(f'{MAIN_PANE} {MESSAGE_ROW}').all()
            
            # Take the last 'limit' nodes
            recent_nodes = message_nodes[-limit:] if len(message_nodes) > limit else message_nodes
            
            import re
            
            for node in recent_nodes:
                sender = "unknown"
                text = ""
                
                html = node.inner_html()
                
                # WhatsApp uses data-pre-plain-text inside the message node which has the sender name
                # e.g., data-pre-plain-text="[2:16 pm, 12/08/2026] Contact Name: "
                pre_plain = re.search(r'data-pre-plain-text="\[.*?\]\s*([^:]+):', html)
                if pre_plain:
                    sender_name = pre_plain.group(1).strip()
                    if sender_name == current_contact:
                        sender = "contact"
                    else:
                        sender = "me"
                else:
                    # System messages or other elements
                    continue
                
                # Get text
                text_locator = node.locator(MESSAGE_TEXT)
                if text_locator.count() > 0:
                    texts = text_locator.all_inner_texts()
                    text = " ".join(texts)
                
                if text:
                    messages.append({"sender": sender, "text": text})
                    
        except Exception as e:
            print(f"Error reading messages: {e}")
            
        return messages

    def send_message(self, expected_contact, text):
        current_contact = self.get_current_contact()
        if not current_contact or current_contact != expected_contact:
            raise ValueError(f"Chat changed. Please reopen the intended conversation. Expected: {expected_contact}, Found: {current_contact}")
            
        try:
            footer = self.page.locator("footer")
            # Typical WhatsApp web input box has contenteditable="true" and data-tab="10"
            input_box = footer.locator('div[contenteditable="true"][data-tab="10"]')
            
            if not input_box.is_visible():
                input_box = footer.locator('div[contenteditable="true"]').first
                
            if not input_box.is_visible():
                raise ValueError("Message input not found")
                
            input_box.fill("")
            input_box.type(text, delay=10)
            
            # Send button typically appears after typing
            send_btn = footer.locator('button[aria-label="Send"]')
            if not send_btn.is_visible():
                send_btn = footer.locator('span[data-icon="send"]').locator('..')
                
            if send_btn.is_visible():
                send_btn.click()
            else:
                input_box.press("Enter")
                
            return True
        except Exception as e:
            raise ValueError(f"Failed to send message: {e}")
