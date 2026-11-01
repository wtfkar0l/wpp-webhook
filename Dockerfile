FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} -w 2 --threads 4 app:app"]
