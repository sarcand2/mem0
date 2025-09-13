# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

WORKDIR /app

# Install only what the server needs (from the server folder)
COPY server/requirements.txt ./requirements.txt

# Use BuildKit cache to speed up subsequent builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -U pip && pip install -r requirements.txt

# Copy only server code (avoid sending the whole repo as image context)
COPY server/ .

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
