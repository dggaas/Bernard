FROM python:3.7-alpine

WORKDIR /app

COPY requirements.txt ./
RUN set -x \
    && apk add --no-cache --virtual .build-dependencies \
        git \
        autoconf \
        g++ \
        make \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-dependencies

COPY . .

CMD [ "python", "./__init__.py" ]
