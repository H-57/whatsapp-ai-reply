# These selectors are based on typical WhatsApp Web DOM structures.
# They are kept here so they can be easily updated if WhatsApp changes its DOM.

# The main pane where the active chat is displayed
MAIN_PANE = '#main'

# Selector for the contact name in the header of the active chat
CONTACT_NAME = 'span[data-testid="conversation-info-header-chat-title"]'

# Selectors for message rows
MESSAGE_ROW = 'div[data-id]'
MESSAGE_IN_CLASS = 'message-in' # No longer reliably used by WA
MESSAGE_OUT_CLASS = 'message-out' # No longer reliably used by WA

# Selector for the text within a message (including emojis rendered inline or as text)
MESSAGE_TEXT = 'span.selectable-text, span.copyable-text'
