FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MSM_DATA_DIR=/data

COPY requirements-backend.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-backend.txt

COPY backend ./backend
COPY shared ./shared
COPY alembic ./alembic
COPY alembic.ini .

VOLUME ["/data"]
EXPOSE 8756

CMD ["python", "-m", "uvicorn", "backend.app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8756"]
