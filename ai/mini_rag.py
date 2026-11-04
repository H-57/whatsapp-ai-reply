import re
from typing import List, Tuple

class MiniRAG:
    """
    Lightweight, dependency-free Retrieval-Augmented Generation (RAG) system.
    Chunks documents and retrieves top matching chunks using word-overlap / BM25-style scoring.
    """
    def __init__(self, chunk_size=350, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        
        # Split into paragraphs or sentences first
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            words = p.split()
            if current_len + len(words) <= self.chunk_size:
                current_chunk.append(p)
                current_len += len(words)
            else:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [p]
                current_len = len(words)

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        # If text had no newlines and was one big block, chunk by word count
        if len(chunks) <= 1 and text.strip():
            words = text.split()
            if len(words) > self.chunk_size:
                chunks = []
                step = self.chunk_size - self.chunk_overlap
                for i in range(0, len(words), max(1, step)):
                    chunk = " ".join(words[i:i + self.chunk_size])
                    chunks.append(chunk)

        return chunks

    def retrieve(self, query: str, knowledge_text: str, top_k=3) -> List[str]:
        if not knowledge_text or not knowledge_text.strip() or not query.strip():
            return []

        chunks = self.chunk_text(knowledge_text)
        if not chunks:
            return []

        # If knowledge base is small (under 600 words), return whole text directly
        total_words = len(knowledge_text.split())
        if total_words <= 400:
            return [knowledge_text.strip()]

        # Tokenize query keywords (ignore common stopwords)
        stopwords = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'and', 'or', 'by', 'it', 'this', 'that', 'i', 'you', 'he', 'she',
            'we', 'they', 'me', 'my', 'your', 'what', 'where', 'when', 'how', 'who', 'why',
            'kya', 'hai', 'kaise', 'kab', 'kaha', 'kon', 'ko', 'se', 'me', 'ki', 'ke', 'aur'
        }
        query_words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in query_words if len(w) > 2 and w not in stopwords]

        if not keywords:
            keywords = [w for w in query_words if len(w) > 1]

        scored_chunks: List[Tuple[float, str]] = []

        for chunk in chunks:
            chunk_lower = chunk.lower()
            score = 0.0
            
            # Substring match bonuses and frequency
            for kw in keywords:
                if kw in chunk_lower:
                    count = chunk_lower.count(kw)
                    score += 1.0 + (0.5 * count)
                    # Whole word boundary bonus
                    if re.search(r'\b' + re.escape(kw) + r'\b', chunk_lower):
                        score += 2.0

            # Direct full phrase boost
            if query.lower().strip() in chunk_lower:
                score += 10.0

            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort highest score first
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]

        # If no specific keyword matched, include the first introductory chunk
        if not top_chunks and chunks:
            top_chunks = [chunks[0]]

        return top_chunks
