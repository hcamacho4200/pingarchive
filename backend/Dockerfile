FROM python:3.14.5-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .
RUN mkdir -p /app/data

EXPOSE 8002
CMD ["python", "src/main.py", "execute-api"]