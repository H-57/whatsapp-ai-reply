import os
from google import genai
from dotenv import load_dotenv
from storage.database import Database
from ai.default_prompt import DEFAULT_SYSTEM_PROMPT
from ai.mini_rag import MiniRAG

load_dotenv()

class ReplyGenerator:
    def __init__(self, db: Database = None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.client = None
            return
            
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.db = db if db else Database()
        self.rag = MiniRAG()

    def generate_reply(self, conversation):
        if not self.client:
            return "Error: Please set GEMINI_API_KEY in the .env file and restart the application."
            
        if not conversation:
            return ""

        # Fetch custom system prompt or fallback to default
        system_instruction = self.db.get_setting("system_prompt", DEFAULT_SYSTEM_PROMPT).strip()
        if not system_instruction:
            system_instruction = DEFAULT_SYSTEM_PROMPT

        # Check for knowledge base / RAG context
        kb_entries = self.db.get_knowledge_base()
        rag_context_str = ""
        if kb_entries:
            combined_kb = "\n\n".join([entry[2] for entry in kb_entries])
            # Build query from recent incoming message(s)
            recent_texts = [msg['text'] for msg in conversation[-3:]]
            query = " ".join(recent_texts)
            relevant_chunks = self.rag.retrieve(query=query, knowledge_text=combined_kb, top_k=3)
            
            if relevant_chunks:
                rag_context_str = (
                    "\n=== RELEVANT KNOWLEDGE BASE / BACKGROUND INFO ===\n"
                    "Use the following factual information to accurately answer questions or provide details if relevant:\n"
                    + "\n---\n".join(relevant_chunks) +
                    "\n===================================================\n\n"
                )

        prompt = f"{system_instruction}\n\n{rag_context_str}Conversation History:\n"
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
