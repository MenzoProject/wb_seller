# WB/Ozon Reseller Bot

Production-ready Telegram-бот для автоматизации работы реселлеров Wildberries и Ozon.
Бот заменяет менеджера, который вручную принимает заявки на выкуп товаров с кэшбэком,
контролирует статусы заявок и выплаты.

> **Статус проекта:** в активной разработке. Проект реализуется поэтапно.
> Текущий этап: **планировщик подключён, бизнес-процесс полностью замкнут
> от начала до конца** — от выбора товара пользователем до автоматического
> ежедневного напоминания администраторам о заявках, готовых к выплате.
> Остался последний этап — финальная сборка и ревизия всего проекта.

## Стек технологий

- Python 3.13
- aiogram 3.x
- SQLAlchemy 2.x (Async)
- PostgreSQL 17
- Redis 7
- Alembic
- APScheduler
- Pydantic Settings
- Docker / Docker Compose
- Ruff, Black, mypy

## Архитектура

Проект построен по принципам Clean Architecture с чётким разделением на слои:

```
src/
├── config/                       # Конфигурация приложения (Pydantic Settings)
├── domain/
│   ├── enums/                    # ApplicationStatus, PaymentStatus, UserRole
│   ├── entities/                 # User, Admin, Product, Application, Payment,
│   │                              # UserRequisites, Bank, Log
│   └── exceptions/                # Доменные исключения (DomainError и наследники)
├── infrastructure/
│   └── database/
│       ├── base.py               # Base, TimestampMixin, CreatedAtMixin
│       ├── engine.py             # Database (AsyncEngine + session factory)
│       └── models/                # ORM-модели всех таблиц
│   └── repositories/
│       ├── interfaces/            # Protocol-абстракции репозиториев (включая AdminRepository)
│       └── implementations/       # Реализации репозиториев на SQLAlchemy
├── application/
│   ├── dto/                       # Pydantic DTO для команд сервисов
│   └── services/                  # UserService, AdminService, ProductService,
│                                   # ApplicationService, PaymentService,
│                                   # RequisitesService, StatisticsService
├── bot/
│   ├── bot_instance.py            # Фабрики Bot, Dispatcher, RedisStorage
│   ├── di/container.py            # DIContainer, ServiceContainer
│   ├── middlewares/                # DbSession, Services, UserRegistration,
│   │                               # AdminAccess, AdminRegistration, Throttling, Logging
│   ├── filters/                   # IsAdminFilter, ApplicationStatusFilter
│   ├── states/                    # ApplicationFlowStates, RequisitesStates,
│   │                               # ProductFormStates, ProductSlotsChangeStates
│   ├── texts/user_texts.py        # Текстовые шаблоны пользовательского бота
│   ├── keyboards/user/            # main_menu, catalog, application_flow
│   ├── handlers/user/             # start, application_flow, my_applications,
│   │                               # requisites, catalog, instructions, support
│   ├── handlers/admin/            # admin_start, products_management,
│   │                               # applications_management, payments_management,
│   │                               # statistics
│   ├── keyboards/admin/           # main_menu, products, applications, payments
│   ├── texts/admin_texts.py       # Текстовые шаблоны админ-бота
│   └── utils/admin_notify.py      # Рассылка уведомлений администраторам
└── logging_config/                # Настройка логирования

infrastructure/scheduler/
├── scheduler.py                   # create_scheduler, register_payment_due_job
└── jobs/
    └── payment_due_job.py         # Ежедневная проверка заявок, готовых к выплате

alembic/
├── env.py                        # Асинхронная конфигурация Alembic
├── script.py.mako                # Шаблон новых миграций
└── versions/
    ├── 0001_initial_schema.py    # Первая миграция: полная схема БД
    └── 0002_add_receipt_required.py  # Добавление поля receipt_required в products
```

Подробное описание архитектуры, структуры базы данных и плана разработки по этапам
приведено в проектной документации (см. историю переписки с архитектором проекта).

## Требования

- Docker >= 24.x
- Docker Compose >= 2.x

Либо для локального запуска без Docker:

- Python 3.13
- PostgreSQL 17
- Redis 7

## Установка и запуск (Docker)

1. Скопируйте файл переменных окружения и заполните реальными значениями:

   ```bash
   cp .env.example .env
   ```

   Обязательно укажите:
   - `BOT_TOKEN` — токен бота, полученный от [@BotFather](https://t.me/BotFather)
   - `BOT_ADMIN_IDS` — Telegram ID администраторов через запятую
   - `POSTGRES_PASSWORD` — надёжный пароль базы данных

2. Соберите и запустите контейнеры и примените миграции:

   ```bash
   docker compose up --build -d
   docker compose run --rm bot alembic upgrade head
   docker compose restart bot
   ```

3. Проверьте логи запуска:

   ```bash
   docker compose logs -f bot
   ```

Бот полностью рабочий и реализует весь бизнес-процесс из ТЗ от начала до
конца: отправьте `/start`, чтобы увидеть главное меню пользователя.
«📦 Каталог» → оформление заявки (артикул, скриншот заказа) →
администратор одобряет заказ в панели управления → пользователь
подтверждает получение товара → выбирает/добавляет реквизиты → отзыв
и/или чек (если требуются для товара) → ожидание выплаты →
администратор отмечает выплату произведённой → пользователь получает
уведомление. Все разделы меню («📋 Мои заявки», «💳 Реквизиты»,
«📖 Инструкция», «💬 Поддержка») полностью реализованы.

Если ваш Telegram ID указан в `BOT_ADMIN_IDS`, отправьте боту команду
`/admin`, чтобы открыть панель администратора. Полностью реализованы:
«📦 Товары» (создание мастером, редактирование, скрытие/показ, остаток,
удаление), «📋 Заявки» (очередь на проверку со скриншотом заказа,
одобрение/отклонение/запрос повтора — каждое решение сразу уведомляет
пользователя), «💰 Выплаты» (список ожидающих исполнения, отметка
оплаты) и «📊 Статистика» (сводка по пользователям, товарам, заявкам и
выплатам). Раздел «⚙ Настройки» остаётся заглушкой — он не был
детализирован в исходном ТЗ.

Планировщик APScheduler ежедневно (время задаётся переменными
`SCHEDULER_PAYMENT_CHECK_HOUR`/`_MINUTE`) проверяет заявки в статусе
ожидания выплаты с наступившей расчётной датой и присылает
администраторам сводку в личные сообщения с ботом.

## Миграции базы данных

Схема базы данных описана моделями SQLAlchemy в
`src/infrastructure/database/models/` и версионируется через Alembic.

Применить миграции к запущенному в Docker контейнеру PostgreSQL:

```bash
docker compose up -d postgres
docker compose run --rm bot alembic upgrade head
```

Либо локально (при активном виртуальном окружении и доступной БД):

```bash
alembic upgrade head
```

Создать новую миграцию после изменения моделей:

```bash
alembic revision --autogenerate -m "описание изменений"
```

Откатить последнюю миграцию:

```bash
alembic downgrade -1
```

## Локальный запуск без Docker (для разработки)

1. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. Скопируйте `.env.example` в `.env` и заполните значения.

3. Запустите точку входа:

   ```bash
   python -m src.main
   ```

## Линтинг и форматирование

```bash
ruff check src
ruff format src
black src
mypy src
```

## План разработки

Проект разрабатывается строго поэтапно. Каждый этап оформляется отдельным
самодостаточным ZIP-архивом:

1. ✅ Инициализация проекта (конфигурация, логирование, Docker)
2. ✅ База данных: модели SQLAlchemy, Alembic
3. ✅ Domain-слой: доменные сущности, исключения, enums
4. ✅ Репозитории (интерфейсы + реализации)
5. ✅ Application-слой: DTO и сервисы
6. ✅ Bot core: DI, middlewares, фильтры
7. ✅ Пользовательский бот — часть 1 (меню, каталог, начало заявки)
8. ✅ Пользовательский бот — часть 2 (продолжение заявки, реквизиты, поддержка)
9. ✅ Админ-бот — часть 1 (товары)
10. ✅ Админ-бот — часть 2 (заявки, выплаты, статистика)
11. ✅ Планировщик APScheduler
12. ⏳ Финализация и полная интеграционная проверка

## Лицензия

Proprietary. Все права защищены.
