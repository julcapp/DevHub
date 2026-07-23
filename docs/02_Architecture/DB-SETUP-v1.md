# DevHub PostgreSQL Setup v1

## Назначение

Документ описывает запуск первого слоя Core DB для Engineering Objects.

## Переменная окружения

```powershell
$env:DEVHUB_DATABASE_URL="postgresql+psycopg://devhub:devhub@localhost:5432/devhub"
```

## Установка

```powershell
python -m pip install -r requirements.txt
```

## Применение миграции

```powershell
python -m alembic upgrade head
```

## Откат

```powershell
python -m alembic downgrade base
```

## Созданные объекты

- схема `core`;
- enum `engineering_object_type`;
- enum `engineering_object_status`;
- `core.engineering_objects`;
- `core.object_relations`;
- `core.audit_events`.

## Правила эксплуатации

1. Подключение к БД не выполняется при обычном импорте UI-модулей.
2. Удаление объекта, участвующего в графе, запрещается внешними ключами.
3. История сохраняется через статус `ARCHIVED` и `archived_at`.
4. Отношение объекта с самим собой запрещено.
5. Повтор одного и того же типизированного ребра запрещён уникальным ограничением.
6. Для production пароль не хранится в репозитории и передаётся только через `DEVHUB_DATABASE_URL`.
