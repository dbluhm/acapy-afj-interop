FROM python:3.9-slim-bookworm
WORKDIR /usr/src/app/

RUN apt-get update && apt-get install -y curl git && apt-get clean
RUN pip install pdm

# Setup controller
RUN mkdir wrapper && touch wrapper/__init__.py
COPY pyproject.toml pdm.lock ./
RUN pdm install

COPY wrapper/ wrapper/
COPY tests/ tests/

ENTRYPOINT ["pdm", "run"]
