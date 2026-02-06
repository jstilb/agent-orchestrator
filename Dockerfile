FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Install production dependencies
RUN pip install --no-cache-dir -e .

# Production stage
FROM base AS production
EXPOSE 8000
ENV ORCHESTRATOR_MODE=mock
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM base AS development
COPY tests/ tests/
RUN pip install --no-cache-dir -e ".[dev]"
CMD ["pytest", "-v"]
