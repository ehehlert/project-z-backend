FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /home/appuser

# Copy and install Python dependencies (as root)
COPY requirements.txt .
COPY .env .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Create a non-root user and switch
RUN adduser --disabled-password appuser
USER appuser

# Copy application code (owned by appuser)
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser models ./models

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]