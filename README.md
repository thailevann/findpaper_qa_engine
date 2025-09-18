### Elasticsearch
```bash
docker run -d --name elasticsearch8 -p 9200:9200 -p 9300:9300 ^
  -e "discovery.type=single-node" ^
  -e "xpack.security.enabled=false" ^
  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" ^
  docker.elastic.co/elasticsearch/elasticsearch:8.19.3
```

### Run Backend (FastAPI)
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Mở một cửa sổ CMD/Terminal khác để chạy frontend.

### Run Frontend (React)
```bash
cd frontend_merge
docker compose up --build
```
http://localhost:3000
