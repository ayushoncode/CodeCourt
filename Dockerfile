FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

RUN useradd -m -u 1000 user
WORKDIR /app

COPY --chown=user:user requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

COPY --chown=user:user . /app

USER user

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
