import os
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

class EmbeddingMemory:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", persona_name="default"):
        """
        Initialize a separate index for each persona_name.
        """
        self.persona_name = persona_name
        self.model = SentenceTransformer(model_name)

        # Path to this persona's memory files
        base_dir = os.path.join(os.path.dirname(__file__), "..", "persistentdata", "memory_databases", persona_name)
        os.makedirs(base_dir, exist_ok=True)

        self.index_path = os.path.join(base_dir, "faiss_index.bin")
        self.doc_store_path = os.path.join(base_dir, "doc_store.json")

        self.doc_store = {}
        self.next_id = 0

        # figure out dimension
        example_emb = self.model.encode("hello", convert_to_numpy=True)
        self.dim = len(example_emb)

        # create a flat L2 index
        self.index = faiss.IndexFlatL2(self.dim)

        # attempt to load from disk
        if (os.path.exists(self.index_path)):
            self._load_index()

        if (os.path.exists(self.doc_store_path)):
            self._load_doc_store()

    def _save_index(self):
        logging.info(f"[{self.persona_name}] Saving FAISS index to disk...")
        faiss.write_index(self.index, self.index_path)

    def _load_index(self):
        logging.info(f"[{self.persona_name}] Loading FAISS index from disk...")
        self.index = faiss.read_index(self.index_path)

    def _save_doc_store(self):
        os.makedirs(os.path.dirname(self.doc_store_path), exist_ok=True)
        with open(self.doc_store_path, "w", encoding="utf-8") as f:
            json.dump(self.doc_store, f, indent=2)

    def _load_doc_store(self):
        with open(self.doc_store_path, "r", encoding="utf-8") as f:
            self.doc_store = json.load(f)
        # adjust next_id
        if self.doc_store:
            max_id = max(map(int, self.doc_store.keys()))
            self.next_id = max_id + 1

    def add_text(self, text):
        embedding = self.model.encode(text, convert_to_numpy=True)
        embedding = np.array([embedding], dtype=np.float32)  # shape [1, dim]

        doc_id = str(self.next_id)
        self.next_id += 1
        self.doc_store[doc_id] = {"text": text}

        self.index.add(embedding)

        self._save_doc_store()
        self._save_index()
        return doc_id

    def search(self, query, top_k=3):
        embedding = self.model.encode(query, convert_to_numpy=True)
        embedding = np.array([embedding], dtype=np.float32)
        distances, indices = self.index.search(embedding, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            doc_id = str(idx)
            text = self.doc_store.get(doc_id, {}).get("text", "")
            score = float(dist)
            results.append((text, score))
        return results