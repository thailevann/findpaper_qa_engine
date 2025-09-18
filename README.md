### Elasticsearch
```bash
docker run -d --name elasticsearch8 -p 9200:9200 -p 9300:9300 ^
  -e "discovery.type=single-node" ^
  -e "xpack.security.enabled=false" ^
  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" ^
  docker.elastic.co/elasticsearch/elasticsearch:8.19.3
```
http://localhost:9200

### Run Backend (FastAPI)
```bash
uvicorn app:app --reload
```
http://localhost:8000

### Run Frontend (React)
```bash
cd frontend-paper-search
docker compose up --build
```
http://localhost:3000
