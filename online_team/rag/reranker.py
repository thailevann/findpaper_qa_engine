# reranker.py
import numpy as np
from sentence_transformers import CrossEncoder
from elasticsearch import Elasticsearch
from config import CROSS_ENCODER_MODEL

class PaperReranker:
    def __init__(self, ce_model_name=None):
        self.ce_model = CrossEncoder(ce_model_name or CROSS_ENCODER_MODEL)
        self.es_text = Elasticsearch("http://localhost:9200", request_timeout=120)

    def find_best_chunk_mean(self, pid, query_embeddings, index_name):
        try:
            vec_doc = self.es_text.get(index=index_name, id=pid)["_source"]
        except:
            return None, 0.0

        chunks_vec = vec_doc.get("chunks", [])
        if not chunks_vec:
            return None, 0.0

        best_score = -1
        best_chunk_id = None
        for c in chunks_vec:
            emb = c.get("embedding")
            if not emb:
                continue
            emb = np.array(emb, dtype=np.float32)
            scores = []
            for qvec in query_embeddings:
                qvec = np.array(qvec, dtype=np.float32)
                score = np.dot(qvec, emb) / (np.linalg.norm(qvec)*np.linalg.norm(emb)+1e-8)
                scores.append(score)
            mean_score = np.mean(scores)
            if mean_score > best_score:
                best_score = mean_score
                best_chunk_id = c.get("chunk_id")

        for c in chunks_vec:
            if c.get("chunk_id") == best_chunk_id:
                return c.get("text"), best_score

        return None, best_score

    def rerank(self, query_text, query_embeddings,
               sem_scores, key_scores,
               top_final=20, alpha=1.0, beta=1.0, index_name=None):
        """
        Rerank dựa trên semantic + keyword, sau đó cross-encoder.
        Bỏ hoàn toàn highlight, evidence = chunk semantic
        """
        # --- Normalize scores về [0,1] ---
        max_sem = max(sem_scores.values()) if sem_scores else 1
        max_key = max(key_scores.values()) if key_scores else 1

        final_scores = {}
        all_ids = set(sem_scores.keys()) | set(key_scores.keys())
        for pid in all_ids:
            s = sem_scores.get(pid, 0) / max_sem
            k = key_scores.get(pid, 0) / max_key
            final_scores[pid] = alpha * s + beta * k

        # --- Build results ---
        ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for pid, score in ranked[:top_final]:
            try:
                doc_text = self.es_text.get(index=index_name, id=pid)["_source"]
                title = doc_text.get("title", "")
                abstract = doc_text.get("abstract", "")
            except:
                title, abstract = "", ""

            # --- Lấy evidence luôn từ chunk semantic ---
            best_chunk, sem_score = self.find_best_chunk_mean(pid, query_embeddings, index_name)
            evidence = best_chunk or abstract

            results.append({
                "paper_id": pid,
                "title": title,
                "score": score, 
                "evidence": evidence
            })

        # --- Cross-Encoder rerank ---
        pairs = [(query_text, r["evidence"]) for r in results]
        ce_scores = self.ce_model.predict(pairs)
        for r, ce in zip(results, ce_scores):
            r["cross_score"] = float(ce)
            r["final_score"] = r["score"] + r["cross_score"]

        return sorted(results, key=lambda x: x["final_score"], reverse=True)[:top_final]
