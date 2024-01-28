FROM python:3.9.18-alpine3.19
LABEL maintainer="nikolas"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

COPY ./app /app

WORKDIR /app

EXPOSE 8000

ARG UID=1000
ARG GID=1000

ARG DEV=false

RUN python -m venv /py && \
    apk add --no-cache bash && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ] ; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp


RUN addgroup -S django-user && adduser -S django-user -G django-user


ENV PATH="/py/bin:$PATH"

USER django-user


