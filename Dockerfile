﻿FROM python:3.9.16-alpine

WORKDIR /app

COPY main.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN python -m pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev && \
        pip install -r requirements.txt && \
        apk del .build-deps; \
    else \
        pip install -r requirements.txt; \
    fi && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: the_devil_of_the_rhine (863687441809801246)" \
      commit=$COMMIT \
      description="This bot automatically publishes messages in announcement channels on discord." \
      release=$BUILD_DATE \
      url="https://gitlab.bloodygang.com/Serpensin/autopublisher" \
      version="1.2.2"

CMD ["python3", "main.py"]
