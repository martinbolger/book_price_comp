# syntax=docker/dockerfile:1

# Use the official Playwright image as the base image, which includes Python and Playwright dependencies. 
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Use the system Python across both stages
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install all dependencies but not the local package
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=packages/,target=packages/ \
    uv pip install --editable . --system

# Install dev dependencies in a separate stage
FROM base AS dev

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=packages/,target=packages/ \
    uv pip install ".[dev]" --system
