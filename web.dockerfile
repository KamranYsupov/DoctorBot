FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UWSGI_PROCESSES 4
ENV UWSGI_THREADS 8
ENV UWSGI_HARAKIRI 60
ENV DJANGO_SETTINGS_MODULE 'web.core.settings'

WORKDIR /opt/

COPY pyproject.toml pyproject.toml
RUN mkdir -p /opt/src/static/ && \
    mkdir -p /opt/src/media/  &&  \
    pip install --upgrade pip && \
    pip install 'poetry>=1.4.2' && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev

COPY . .

EXPOSE 8000

COPY ./web/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]