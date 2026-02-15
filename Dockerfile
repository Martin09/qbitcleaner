# ---- Builder stage ----
FROM python:3.12-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies (cached via mount)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---- Final stage ----
FROM python:3.12-alpine

# Metadata for GitHub Packages
LABEL org.opencontainers.image.source="https://github.com/martin09/qbitcleaner"
LABEL org.opencontainers.image.description="Automatically clean up qBittorrent seeding list"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY qbitcleaner.py config.example.yaml ./
RUN cp config.example.yaml config.yaml

# Use the venv Python directly — no uv needed at runtime
ENTRYPOINT ["/app/.venv/bin/python", "qbitcleaner.py"]
