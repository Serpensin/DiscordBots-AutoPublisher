FROM python:3.9.16-alpine

WORKDIR /app

COPY main.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN python -m pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev; \
    fi
RUN pip install -r requirements.txt

LABEL maintainer="./𝕾𝖊𝖗𝖕𝖊𝖓𝖘𝖎𝖓.𝖘𝖍#0007"
LABEL commit=$COMMIT
LABEL description="AutoPublisher for messages in announcement-channels."
LABEL release=$BUILD_DATE
LABEL url="https://gitlab.bloodygang.com/Serpensin/autopublisher"
LABEL VERSION="1.2.0"

CMD ["python3", "main.py"]
