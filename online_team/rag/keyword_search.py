from elasticsearch import Elasticsearch

class KeywordSearch:
    def __init__(self, es_url="http://localhost:9200", index_name="papers_text"):
        self.es = Elasticsearch(es_url, request_timeout=120)
        self.index_name = index_name

    def search(self, query_text, top_k=50, filters: dict = None):
        """
        filters: dict, ví dụ {"update_date": "2020-01-01:2025-12-31"}
        """
        body = {
            "size": top_k,
            "_source": ["paper_id", "title", "abstract"],
            "query": {
                "bool": {
                    "must": [],  # nơi đặt filter
                    "should": [
                        {"match_phrase": {"title": {"query": query_text, "boost": 5}}},
                        {"match_phrase": {"abstract": {"query": query_text, "boost": 3}}},
                        {"multi_match": {"query": query_text, "fields": ["title^2", "abstract"], "type": "best_fields"}}
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "abstract": {}
                }
            }
        }

        # --- Apply filters ---
        if filters:
            for field, value in filters.items():
                # Nếu filter là range dạng "start:end"
                if ":" in value:
                    gte, lte = value.split(":")
                    body["query"]["bool"]["must"].append({"range": {field: {"gte": gte, "lte": lte}}})
                else:
                    # filter exact match
                    body["query"]["bool"]["must"].append({"term": {field: value}})

        res = self.es.search(index=self.index_name, body=body)
        scores = {}
        highlights = {}

        raw_scores = [hit["_score"] for hit in res["hits"]["hits"]]
        max_score = max(raw_scores) if raw_scores else 1  # tránh chia 0

        for hit in res["hits"]["hits"]:
            pid = hit["_source"]["paper_id"]
            scores[pid] = hit["_score"] / max_score  # chuẩn hóa về 0-1
            highlights[pid] = hit.get("highlight", {})

        return scores, highlights
