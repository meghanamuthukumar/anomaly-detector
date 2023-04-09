FROM python:3.7-alpine
WORKDIR /app
COPY requirements.txt requirements.txt
COPY . .
RUN apk update && apk upgrade
RUN apk add linux-headers
RUN apk update && apk add python3-dev
RUN apk update && apk add gcc
RUN apk update && apk add libc-dev
RUN apk update && apk add libffi-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python3", "-u", "anomaly-detector.py"]