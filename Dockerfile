FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN pytest

EXPOSE 80
CMD ["uvicorn", "main_web:app", "--host", "0.0.0.0", "--port", "80"]
