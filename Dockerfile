FROM python:3.11-slim

# tăng timeout
ENV PIP_DEFAULT_TIMEOUT=200

WORKDIR /app

# chỉ copy requirements trước
COPY requirements.txt .

# cài đặt gói trước
RUN pip install --no-cache-dir -r requirements.txt
# sau đó mới copy code
COPY . .

CMD ["python", "app.py"]
