FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.14-slim

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY . .
RUN uv sync --no-cache

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
