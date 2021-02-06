FROM python:3.9.1-buster

WORKDIR /usr/src/app

COPY . ./
RUN pip install --no-cache-dir -U -r requirements.txt

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]