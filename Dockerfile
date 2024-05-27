FROM python:3.12.3-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY *.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libc-dev linux-headers rust cargo g++ && \
    python -m pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: pika.pika.no.mi (970119359840284743)" \
      commit=$COMMIT \
      description="This bot automatically publishes messages in announcement channels on discord." \
      release=$BUILD_DATE \
      url="https://gitlab.bloodygang.com/Serpensin/autopublisher" \
      version="1.6.4"

CMD ["python3", "main.py"]
