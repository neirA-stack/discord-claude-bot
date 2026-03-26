FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py claude_client.py config.py db.py utils.py ./

CMD ["python", "bot.py"]
