from elasticsearch import Elasticsearch
import numpy as np

class SemanticSearch:
    def __init__(self, es_url="http://localhost:9200", index_name="papers_vectors"):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name

    def search(self, query_embedding, top_k=50, filters: dict = None):
        """
        filters: dict, ví dụ {"update_date": "2020-01-01:2025-12-31"}
        """
        # --- Base query: match all ---
        base_query = {"match_all": {}}

        # --- Apply filters ---
        if filters:
            must_clauses = []
            for field, value in filters.items():
                if ":" in value:
                    gte, lte = value.split(":")
                    must_clauses.append({"range": {field: {"gte": gte, "lte": lte}}})
                else:
                    must_clauses.append({"term": {field: value}})
            base_query = {"bool": {"must": must_clauses}}

        body = {
            "size": top_k,
            "_source": ["paper_id"],
            "query": {
                "script_score": {
                    "query": base_query,
                    "script": {
                        "source": """
                            double maxScore = 0;
                            if (doc['title_embedding'].size() != 0) {
                                double score = cosineSimilarity(params.qvec, 'title_embedding');
                                if (score > maxScore) maxScore = score;
                            }
                            if (doc['abstract_embedding'].size() != 0) {
                                double score = cosineSimilarity(params.qvec, 'abstract_embedding');
                                if (score > maxScore) maxScore = score;
                            }
                            if (doc['chunks.embedding'].size() != 0) {
                                for (int i=0; i<doc['chunks.embedding'].size(); i++) {
                                    double score = cosineSimilarity(params.qvec, doc['chunks.embedding'][i]);
                                    if (score > maxScore) maxScore = score;
                                }
                            }
                            return maxScore;
                        """,
                        "params": {"qvec": query_embedding}
                    }
                }
            }
        }

        res = self.es.search(index=self.index_name, body=body)
        scores = {hit["_source"]["paper_id"]: hit["_score"] for hit in res["hits"]["hits"]}
        return scores
