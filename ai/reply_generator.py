import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class ReplyGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.client = None
            return
            
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    def generate_reply(self, conversation):
        if not self.client:
            return "Error: Please set GEMINI_API_KEY in the .env file and restart the application."
            
        if not conversation:
            return ""
            
        prompt = "Generate a short, natural, and concise reply to this WhatsApp conversation. Respond as 'me'. Do not include quotes or prefixes like 'Me:' in your output.\n\n"
        for msg in conversation:
            sender = "Contact" if msg["sender"] == "contact" else "Me"
            prompt += f"{sender}: {msg['text']}\n"
            
        prompt += "\nMe:"
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Error: AI generation failed - {e}"
