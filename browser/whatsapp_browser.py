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

            # Use JavaScript evaluation to accurately extract messages, texts, and emojis
            # WhatsApp Web renders emojis either as unicode characters or as <img alt="😊" data-plain-text="😊">
            js_script = """
            (currentContact) => {
                const main = document.querySelector('#main');
                if (!main) return [];

                // Message rows usually have data-id attribute
                const rows = Array.from(main.querySelectorAll('div[data-id]'));
                const results = [];

                for (const row of rows) {
                    // 1. Identify sender from data-pre-plain-text attribute
                    // e.g. [10:30 am, 12/08/2026] Contact Name:
                    const prePlainEl = row.querySelector('[data-pre-plain-text]') || row;
                    const prePlainText = prePlainEl.getAttribute('data-pre-plain-text') || '';
                    
                    let sender = 'unknown';
                    const match = prePlainText.match(/\[.*?\]\s*([^:]+):/);
                    if (match) {
                        const senderName = match[1].trim();
                        sender = (senderName === currentContact.trim()) ? 'contact' : 'me';
                    } else {
                        // Check if message row has message-in or message-out classes
                        if (row.classList.contains('message-in')) {
                            sender = 'contact';
                        } else if (row.classList.contains('message-out')) {
                            sender = 'me';
                        } else {
                            continue;
                        }
                    }

                    // 2. Extract message text including emojis
                    // Look for copyable-text container or selectable-text
                    const textContainer = row.querySelector('.copyable-text, .selectable-text');
                    let messageText = '';

                    if (textContainer) {
                        // Extract text and substitute <img> emojis with their alt / data-plain-text attribute
                        const clone = textContainer.cloneNode(true);
                        const emojiImgs = clone.querySelectorAll('img[data-plain-text], img[alt]');
                        emojiImgs.forEach(img => {
                            const emojiChar = img.getAttribute('data-plain-text') || img.getAttribute('alt') || '';
                            const textNode = document.createTextNode(emojiChar);
                            img.parentNode.replaceChild(textNode, img);
                        });
                        messageText = (clone.textContent || '').trim();
                    }

                    // Fallback: check standalone emoji images if textContainer is missing or empty
                    if (!messageText) {
                        const standaloneEmoji = row.querySelectorAll('img[data-plain-text], img[alt]');
                        const emojis = [];
                        standaloneEmoji.forEach(img => {
                            const char = img.getAttribute('data-plain-text') || img.getAttribute('alt');
                            if (char) emojis.push(char);
                        });
                        if (emojis.length > 0) {
                            messageText = emojis.join('');
                        }
                    }

                    // Remove time stamps or invisible unicode formatting markers
                    messageText = messageText.replace(/[\\u200e\\u200f\\u202a-\\u202e]/g, '').trim();

                    if (messageText) {
                        results.push({ sender, text: messageText });
                    }
                }

                return results;
            }
            """
            
            raw_messages = self.page.evaluate(js_script, current_contact)
            if raw_messages:
                messages = raw_messages[-limit:] if len(raw_messages) > limit else raw_messages
                    
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
                
            # Clear and focus input
            input_box.click()
            
            # Use page.keyboard.insert_text or execCommand to insert text containing multi-byte emojis reliably
            try:
                # insert_text preserves Unicode emojis correctly in contenteditable divs
                self.page.keyboard.insert_text(text)
            except Exception:
                input_box.fill("")
                input_box.type(text, delay=10)
            
            self.page.wait_for_timeout(300)
            
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
