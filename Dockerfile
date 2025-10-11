FROM python:3.13-slim

# системные пакеты (таймзона и прочее)
RUN apt-get update && apt-get install -y tzdata \
    && ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

# переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN pip install poetry

RUN poetry config virtualenvs.in-project false
RUN poetry install --no-root

CMD poetry run python main.py
