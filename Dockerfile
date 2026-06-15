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
RUN python3 -m playwright install chromium --with-deps

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# 2. Copy ONLY the files needed for the install
# This includes the manifest and your local package folders
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/uv to speed up subsequent builds.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install . 


# --- STAGE 2: Dev Environment (Used by VS Code / Compose) ---
FROM base AS dev_container
COPY . .

# --- STAGE 3: Lambda Environment (Used by Terraform / Floci) ---
FROM base AS lambda_runtime
RUN uv pip install awslambdaric

# 2. Download the Runtime Interface Emulator (RIE)
# This allows the container to run locally without the 'KeyError'
RUN curl -Lo /usr/local/bin/aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie && \
    chmod +x /usr/local/bin/aws-lambda-rie

COPY . .

# 3. Use the RIE as a wrapper
# If the container detects it's running locally, RIE will handle the API; 
# if it's in AWS, it passes through to the RIC.
ENTRYPOINT [ "/usr/local/bin/aws-lambda-rie", "/usr/bin/python", "-m", "awslambdaric" ]

CMD [ "scraper.run_injestion_cycle.handler" ]