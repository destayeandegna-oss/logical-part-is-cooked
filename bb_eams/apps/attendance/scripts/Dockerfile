FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add bb_eams to python path to allow imports like 'apps.accounts'
ENV PYTHONPATH="${PYTHONPATH}:/app/bb_eams"

CMD ["gunicorn", "bb_eams.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]