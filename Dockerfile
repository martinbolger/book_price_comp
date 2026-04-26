# syntax=docker/dockerfile:1

# Use the official Playwright image as the base image, which includes Python and Playwright dependencies. 
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble as base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/uv to speed up subsequent builds.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --editable . --no-cache-dir

# Install Playwright browsers after dependencies are installed
RUN playwright install chromium
