# syntax=docker/dockerfile:1

# --- STAGE 1: Shared Base ---
# Use the official Playwright image as the base image, which includes Python and Playwright dependencies. 
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble AS base

# Install make and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. THE BIG DOWNLOAD (Optimized for caching)
# Using 'python3 -m playwright' is safer than just 'playwright'
# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/uv to speed up subsequent builds.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install playwright --system

# Tell Playwright to use a permanent, global system directory
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# This step will now be perfectly cached by Docker's layer system
RUN python3 -m playwright install chromium --with-deps

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

# --- STAGE 2: Dev Environment (Used by VS Code / Compose) ---
FROM base AS dev
# Because Docker Compose mounts your local directory `.:/app` at runtime,
# we only copy the bare setup structures to make sure the environment is valid.
COPY pyproject.toml uv.lock ./

# --- INSERT THIS LINE TO BUST THE CACHE FOR EVERYTHING BELOW IT ---
# Pull down your dev tools directly without compiling an editable root wrapper
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv pip install . --system --extra dev
