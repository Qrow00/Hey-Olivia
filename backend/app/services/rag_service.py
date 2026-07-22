import os
import json
import time
import hashlib
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    id: str
    source: str
    chunk_index: int
    text: str
    embedding: Optional[np.ndarray] = field(default=None, repr=False)
    metadata: dict = field(default_factory=dict)


class RAGService:
    def __init__(self):
        self._data_dir = Path(__file__).parent.parent.parent / "data" / "rag"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._chunks: list[DocumentChunk] = []
        self._embeddings_file = self._data_dir / "embeddings.npy"
        self._metadata_file = self._data_dir / "metadata.json"
        self._embedding_model = "nomic-embed-text"
        self._chunk_size = 500
        self._chunk_overlap = 50
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    chunk = DocumentChunk(
                        id=entry["id"],
                        source=entry["source"],
                        chunk_index=entry["chunk_index"],
                        text=entry["text"],
                        metadata=entry.get("metadata", {}),
                    )
                    self._chunks.append(chunk)
                if self._embeddings_file.exists() and self._chunks:
                    embeddings = np.load(str(self._embeddings_file))
                    for i, chunk in enumerate(self._chunks):
                        if i < len(embeddings):
                            chunk.embedding = embeddings[i]
                print(f"[RAG] Loaded {len(self._chunks)} chunks")
            except Exception as e:
                print(f"[RAG] Load error: {e}")
        self._loaded = True

    def _save(self):
        try:
            data = []
            for chunk in self._chunks:
                data.append({
                    "id": chunk.id,
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                })
            with open(self._metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            embeddings = np.array([c.embedding for c in self._chunks if c.embedding is not None])
            if len(embeddings) > 0:
                np.save(str(self._embeddings_file), embeddings)
            print(f"[RAG] Saved {len(self._chunks)} chunks")
        except Exception as e:
            print(f"[RAG] Save error: {e}")

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self._chunk_size]
            chunks.append(" ".join(chunk_words))
            i += self._chunk_size - self._chunk_overlap
        return chunks if chunks else [text]

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        import ollama
        try:
            response = ollama.embeddings(model=self._embedding_model, prompt=text)
            return np.array(response["embedding"], dtype=np.float32)
        except Exception as e:
            print(f"[RAG] Embedding error: {e}")
            return None

    def _get_embeddings_batch(self, texts: list[str]) -> list[Optional[np.ndarray]]:
        import ollama
        results = []
        for text in texts:
            try:
                response = ollama.embeddings(model=self._embedding_model, prompt=text)
                results.append(np.array(response["embedding"], dtype=np.float32))
            except Exception as e:
                print(f"[RAG] Batch embedding error: {e}")
                results.append(None)
        return results

    def ingest_text(self, text: str, source: str = "user_input", metadata: dict = None) -> int:
        self._load()
        chunks_text = self._chunk_text(text)
        embeddings = self._get_embeddings_batch(chunks_text)
        
        count = 0
        for i, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
            if embedding is None:
                continue
            chunk_id = hashlib.md5(f"{source}:{i}:{chunk_text[:100]}".encode()).hexdigest()
            chunk = DocumentChunk(
                id=chunk_id,
                source=source,
                chunk_index=i,
                text=chunk_text,
                embedding=embedding,
                metadata=metadata or {},
            )
            self._chunks.append(chunk)
            count += 1
        
        self._save()
        return count

    def ingest_file(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                text = self._read_pdf(str(path))
            elif suffix in (".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".log", ".html", ".xml"):
                text = path.read_text(encoding="utf-8", errors="ignore")
            elif suffix in (".docx", ".doc"):
                return {"status": "error", "message": "DOCX support requires python-docx. Use .txt or .md files."}
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {str(e)}"}
        
        count = self.ingest_text(text, source=str(path), metadata={"filename": path.name, "type": suffix})
        return {"status": "success", "file": path.name, "chunks_added": count, "total_chunks": len(self._chunks)}

    def _read_pdf(self, file_path: str) -> str:
        try:
            import subprocess
            escaped_path = file_path.replace("'", "\\'")
            code = f"""
import sys
try:
    from PyPDF2 import PdfReader
    reader = PdfReader('{escaped_path}')
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    print(text)
except:
    try:
        import subprocess
        r = subprocess.run(['pdftotext', '{escaped_path}', '-'], capture_output=True, text=True)
        print(r.stdout)
    except:
        print('')
"""
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout
        except Exception:
            return ""

    def search(self, query: str, top_k: int = 5, threshold: float = 0.3) -> list[dict]:
        self._load()
        if not self._chunks:
            return []
        
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []
        
        scored = []
        for chunk in self._chunks:
            if chunk.embedding is None:
                continue
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            if similarity >= threshold:
                scored.append({"chunk": chunk, "score": float(similarity)})
        
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        results = []
        seen_sources = set()
        for item in scored[:top_k * 2]:
            chunk = item["chunk"]
            source_key = chunk.source
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)
            results.append({
                "text": chunk.text,
                "source": chunk.source,
                "score": item["score"],
                "metadata": chunk.metadata,
            })
            if len(results) >= top_k:
                break
        
        return results

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def get_context_for_llm(self, query: str, top_k: int = 3) -> str:
        results = self.search(query, top_k=top_k)
        if not results:
            return ""
        
        context_parts = ["[Retrieved from knowledge base]"]
        for r in results:
            source = Path(r["source"]).name if r["source"] != "user_input" else "conversation"
            context_parts.append(f"\n--- Source: {source} (relevance: {r['score']:.2f}) ---")
            context_parts.append(r["text"])
        
        return "\n".join(context_parts)

    def get_stats(self) -> dict:
        self._load()
        sources = {}
        for chunk in self._chunks:
            src = chunk.source
            sources[src] = sources.get(src, 0) + 1
        return {
            "total_chunks": len(self._chunks),
            "sources": sources,
            "embedding_model": self._embedding_model,
        }

    def clear_source(self, source: str) -> int:
        self._load()
        before = len(self._chunks)
        self._chunks = [c for c in self._chunks if c.source != source]
        removed = before - len(self._chunks)
        self._save()
        return removed

    def clear_all(self) -> int:
        self._load()
        count = len(self._chunks)
        self._chunks = []
        self._save()
        return count


rag_service = RAGService()
