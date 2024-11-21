FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/

COPY pyproject.toml pyproject.toml
RUN mkdir -p /opt/src/static/ && \
    mkdir -p /opt/src/media/  &&  \
    pip install --upgrade pip && \
    pip install 'poetry>=1.4.2' && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev


CMD ['python' 'bot/main.py']