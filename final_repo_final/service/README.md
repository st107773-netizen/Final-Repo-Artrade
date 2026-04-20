# SLA service: ingestion, metrics, API

Проект закрывает пункты 1–9 из технического списка:

1. **Аудит датасета**: скрипт `scripts/audit_dataset.py` считает пустые timestamps, аномалии и рекомендации по обработке.
2. **ERD**: файл `erd.mmd` содержит схему БД для двух воронок: CRM и доставка.
3. **Идемпотентная загрузка**: `scripts/load_csv.py` делает upsert по `lead_id`, кросс-проверяет дублирующие поля и сохраняет события обеих воронок.
4. **SLA-1 + ручная проверка**: `scripts/manual_check_sla1.py` выводит 5–10 строк с формулой `sale_ts -> handed_to_delivery_ts`.
5. **Остальные метрики**: рассчитываются в `app/services/sla.py`.
6. **API**: `GET /api/sla/b2c/summary`.
7. **Конфиг нормативов**: `config/norms.yml`.
8. **Правила исключений**: lifecycle_incomplete / outcome_unknown / отрицательные лаги / total_cycle > 60 — централизованы в конфиге и коде расчёта.
9. **README + docker-compose**: включены.

## Структура проекта

- `app/models.py` — SQLAlchemy-модели
- `app/services/loader.py` — загрузка и идемпотентный upsert
- `app/services/sla.py` — расчёт SLA
- `app/routers/sla.py` — API-роуты
- `scripts/audit_dataset.py` — аудит качества датасета
- `scripts/load_csv.py` — загрузка CSV в БД
- `scripts/manual_check_sla1.py` — ручная проверка SLA-1
- `config/norms.yml` — нормативы и правила исключений
- `erd.mmd` — ERD

## SLA-метрики в этом шаблоне

Предположения для рабочего каркаса:
- **SLA-1**: время от `sale_ts` до `handed_to_delivery_ts`
- **SLA-2**: время от `handed_to_delivery_ts` до `issued_or_pvz_ts`
- **SLA-3**: время от `issued_or_pvz_ts` до `outcome_ts`
- **Total cycle**: время от `sale_ts` до `outcome_ts`

Если в вашем документе `ts_sla_v2` формулы отличаются, поменяйте их только в `app/services/sla.py` и нормативы в `config/norms.yml`.

## Как запускать

### 1. Поднять сервисы
```bash
docker-compose up --build
```

### 2. Инициализировать таблицы
```bash
docker-compose exec api python -m scripts.init_db
```

### 3. Аудит датасета
```bash
docker-compose exec api python -m scripts.audit_dataset   --csv /app/data/MIPT_hackathon_dataset_sla_hackathon.csv
```

### 4. Загрузить данные
```bash
docker-compose exec api python -m scripts.load_csv   --csv /app/data/MIPT_hackathon_dataset_sla_hackathon.csv   --source mipt
```

### 5. Ручная проверка SLA-1 на 10 строках
```bash
docker-compose exec api python -m scripts.manual_check_sla1 --limit 10
```

### 6. Получить summary по API
```bash
curl http://localhost:8000/api/sla/b2c/summary
```

## Что считать нормой по пустым timestamps

Логика обработки:
- `received_ts`, `rejected_ts`, `returned_ts`, `closed_ts` могут быть пустыми, если заказ ещё не завершён.
- `handed_to_delivery_ts` и `issued_or_pvz_ts` не должны использоваться для SLA, если этап до них не наступил.
- строки с `lifecycle_incomplete = true` считаются технически недостоверными и исключаются из строгих SLA.
- строки с `outcome_unknown = true` исключаются из итоговых сквозных метрик.
- отрицательные лаги интерпретируются как нарушение порядка событий, а не как реальный “отрицательный срок”.

## Идемпотентность

Загрузка реализована через upsert по `lead_id`:
- повторная загрузка не создаёт дублей;
- обновляет поля лида;
- пересобирает события CRM и доставки;
- пересчитывает SLA-метрики.

## Что нужно адаптировать под прод
- полноценную миграцию Alembic;
- аутентификацию API;
- мониторинг и логирование;
- CI/CD;
- отдельные таблицы справочников статусов и каналов.
