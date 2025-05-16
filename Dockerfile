FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /usr/src/app/

RUN apt-get update && apt-get install -y git && apt-get clean

# Setup controller
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY wrapper/ wrapper/
COPY tests/ tests/

ENTRYPOINT ["uv", "run"]
