FROM python:3.9.18-alpine3.19
LABEL maintainer="nikolas"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts

COPY ./app /app

WORKDIR /app

EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    apk add --no-cache bash && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev libffi-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ] ; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    addgroup -S django-user && \
    adduser -S django-user -G django-user && \
    mkdir -p /vol/web/media/uploads && \
    mkdir -p /vol/web/static/ && \
    chown -R django-user:django-user /vol && \
    chmod -R 777 /vol && \
    chmod +x /scripts/*

ENV PATH="/scripts:/py/bin:$PATH"

USER django-user


CMD ["run.sh"]
