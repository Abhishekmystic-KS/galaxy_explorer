FROM python:3.12-slim

# Install system dependencies needed for compiling packages or general operation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv using the official binary image injection
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself or dev packages
RUN uv sync --frozen --no-dev --no-install-project

# Copy project files
COPY . .

# Final sync to install the project
RUN uv sync --frozen --no-dev

# Expose the FastAPI application port
EXPOSE 8000

# Execute FastAPI via uvicorn
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
