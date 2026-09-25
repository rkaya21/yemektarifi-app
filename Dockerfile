FROM python:3.12-alpine3.20
LABEL maintainer="recepeneskaya.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements /tmp/requirements
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    /py/bin/pip install -r /tmp/requirements/base.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements/dev.txt ; \
    fi && \
    rm -rf /tmp/requirements && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
    mkdir -p /app/media && \
    chown -R django-user:django-user /app/media && \
    chmod -R 755 /app/media

ENV PATH="/py/bin:$PATH"

USER django-user
