FROM python:3.9-slim

RUN apt-get update && apt-get install git -y

RUN python -m pip install --upgrade pip && pip install poetry

WORKDIR /usr/src/gdtbot

COPY poetry.lock pyproject.toml ./
COPY baseballclerk ./baseballclerk

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

WORKDIR /baseballclerk/

ENTRYPOINT [ "python", "-OO", "-u", "-m", "baseballclerk" ]
