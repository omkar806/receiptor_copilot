FROM python:3.12.2

ENV PYTHONUNBUFFERED True-slim

WORKDIR /app

ENV PORT=8080

EXPOSE $PORT

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app","--host" ,"0.0.0.0", "--port", "8080"]
