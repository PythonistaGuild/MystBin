FROM python:3.9-slim

WORKDIR /usr/src/app

COPY . ./
RUN pip install --no-cache-dir -U -r requirements.txt
ENV ISDOCKER=true

CMD ["python", "main.py"]
