import os
import json
import sqlite3
import numpy as np
import logging
from datetime import datetime, timezone
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Any

class SQLMemory:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", persona_name: str = "default") -> None:
        """
        Initialize a SQL-based memory system for each persona.
        """
        self.persona_name = persona_name
        try:
            self.model = SentenceTransformer(model_name)
            logging.info(f"Loaded sentence transformer model for {persona_name}")
        except Exception as e:
            logging.error(f"Failed to load sentence transformer model: {e}")
            self.model = None
        
        # Base directory for persistent data
        self.base_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "persistentdata", 
            "memory_databases",
            persona_name
        )
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Path to this persona's memory database
        self.db_path = os.path.join(self.base_dir, "memory.db")
        # Path to chat_history.json (for compatibility with JS)
        self.chat_history_path = os.path.join(self.base_dir, "chat_history.json")
        
        logging.info(f"Using database at: {self.db_path}")
        
        self._initialize_database()
        
        # Cache for short-term memory
        self.stm_cache: List[dict] = []
        self.max_stm_size = 3
        
        # Load existing chat history into STM buffer
        self._load_stm_from_history()
        
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    text TEXT,
                    embedding BLOB,
                    role TEXT,
                    type TEXT,
                    importance REAL DEFAULT 1.0
                )''')
                conn.commit()
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            
    def _load_stm_from_history(self) -> None:
        """Load recent chat history into STM buffer."""
        try:
            if os.path.exists(self.chat_history_path):
                with open(self.chat_history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                recent = history[-self.max_stm_size:] if history else []
                for entry in recent:
                    if "role" in entry and "content" in entry:
                        self.stm_cache.append({
                            "role": entry["role"],
                            "content": entry["content"]
                        })
        except Exception as e:
            logging.error(f"Error loading chat history into STM: {e}")
            
    def add_memory(self, text: str, role: str = "assistant", memory_type: str = "conversation") -> None:
        """Add a memory entry with its embedding."""
        if not text or not isinstance(text, str):
            logging.warning(f"Attempted to add invalid memory: {text}")
            return
            
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Update JSON chat history for JS compatibility
        if role in ["user", "assistant"] and memory_type == "conversation":
            try:
                history = []
                if os.path.exists(self.chat_history_path):
                    try:
                        with open(self.chat_history_path, "r", encoding="utf-8") as f:
                            history = json.load(f)
                    except json.JSONDecodeError:
                        logging.warning("Invalid JSON in chat history file, creating new")
                entry = {
                    "timestamp": timestamp,
                    "role": role,
                    "content": text
                }
                history.append(entry)
                with open(self.chat_history_path, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2)
                # Update STM buffer
                self.stm_cache.append({"role": role, "content": text})
                if len(self.stm_cache) > self.max_stm_size:
                    self.stm_cache.pop(0)
            except Exception as e:
                logging.error(f"Error updating chat history: {e}")
        
        # Store with vector embedding in SQLite
        try:
            embedding_bytes = None
            if self.model:
                embedding = self.model.encode(text, convert_to_numpy=True)
                embedding_bytes = embedding.tobytes()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memory_entries (timestamp, text, embedding, role, type) VALUES (?, ?, ?, ?, ?)",
                    (timestamp, text, embedding_bytes, role, memory_type)
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Error adding memory to database: {e}")
        
    def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[Any, float, int]]:
        """Find memories similar to the query using vector similarity."""
        if not query or not isinstance(query, str):
            return []
            
        if not self.model:
            logging.warning("No embedding model available")
            return []
            
        try:
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, text, embedding, importance FROM memory_entries WHERE embedding IS NOT NULL")
                results = []
                for mem_id, text, embedding_bytes, importance in cursor.fetchall():
                    if not embedding_bytes:
                        continue
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                    norm_q = np.linalg.norm(query_embedding)
                    norm_doc = np.linalg.norm(embedding)
                    similarity = 0 if norm_q == 0 or norm_doc == 0 else np.dot(query_embedding, embedding) / (norm_q * norm_doc)
                    weighted_similarity = similarity * (importance or 1.0)
                    if similarity > 0.3:
                        results.append((text, weighted_similarity, mem_id))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            logging.error(f"Error searching similar memories: {e}")
            return []
    
    def get_stm(self) -> List[dict]:
        """Get the short-term memory buffer."""
        return self.stm_cache
    
    def get_chat_history(self) -> List[dict]:
        """Get chat history from JSON file."""
        try:
            if os.path.exists(self.chat_history_path):
                with open(self.chat_history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"Error reading chat history: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all memories for this persona."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memory_entries")
                conn.commit()
            with open(self.chat_history_path, "w", encoding="utf-8") as f:
                json.dump([], f)
            self.stm_cache = []
            logging.info(f"Cleared all memories for persona {self.persona_name}")
        except Exception as e:
            logging.error(f"Error clearing memories: {e}")

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Any, float, int]]:
        """
        Compatibility method that matches the signature of EmbeddingMemory.search()
        """
        return self.search_similar(query, top_k)
