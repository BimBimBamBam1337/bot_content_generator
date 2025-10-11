# test_bot

Краткое описание проекта:
Telegram-бот для интернет-магазина с корзиной, заказами и системой категорий.

## Установка

1. Клонируем репозиторий:
```bash
git clone <repo_url>
cd <project_folder>
```
2. Создаём .env файл и добавляем:
```
TOKEN=<токен бота>
POSTGRES_DSN=postgresql+asyncpg://<пользователь>:<пароль>@postgres:5432/<название_бд>
DB_USER=<пользователь>
DB_PASS=<пароль>
DB_NAME=<название_бд>
REDIS_PORT=<порт для редиса>
```

После установки нужно запустить команду make up, а послед поднятия всех сервисов
написать make migrate

## Архитектура

- `src/telegram` – хендлеры, клавиатуры, тексты
- `src/database` – модели SQLAlchemy, UnitOfWork, репозитории
- `src/services` – бизнес-логика (CartService, UserService, OrderService)
- `src/config` – настройки, загрузка .env
- `src/main.py` – точка входа приложения
## База данных

- Таблица `users`: id, telegram_id, name, phone, address, is_admin, created_at, updated_at  
- Таблица `categories`: id, name, created_at, updated_at  
- Таблица `products`: id, name, description, price, photo_url, stock, category_id, created_at, updated_at  
- Таблица `carts`: id, user_id, created_at, updated_at  
- Таблица `cart_items`: id, cart_id, product_id, quantity, price_at_add, created_at, updated_at  
- Таблица `orders`: id, order_number, user_id, total, status, delivery_method, created_at, updated_at  
- Таблица `order_items`: id, order_id, product_id, quantity, price, created_at, updated_at  

Связи: users→carts→cart_items, users→orders→order_items, categories→products
