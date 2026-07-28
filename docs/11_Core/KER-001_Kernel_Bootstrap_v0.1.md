# KER-001 — Kernel Bootstrap v0.1

**Статус:** реализовано в рамках Sprint 1  
**Версия Kernel:** 0.1.0

## 1. Назначение

Kernel Bootstrap вводит официальную последовательность запуска DevHub:

```text
app.main
  -> Bootstrap
  -> Kernel
  -> Service Registry
  -> Capability Registry
  -> Event Bus
  -> существующий PySide6 UI
```

Bootstrap не содержит бизнес-логику Git, GitHub, AI или конкретных проектов.

## 2. Реализованные компоненты

- `core/common/service.py` — базовый контракт сервиса, состояния и здоровье;
- `core/registry/service_registry.py` — регистрация сервисов и проверка зависимостей;
- `core/capabilities/capability_registry.py` — регистрация провайдеров возможностей;
- `core/events/event_bus.py` — синхронная шина событий Kernel v0.1;
- `core/kernel/kernel.py` — жизненный цикл и метрики ядра;
- `core/bootstrap/bootstrap.py` — запуск ядра и передача управления UI;
- `tests/test_kernel.py` — базовые модульные тесты.

## 3. Жизненный цикл сервиса

```text
Created -> Initialized -> Starting -> Ready -> Stopping -> Stopped
```

Дополнительные состояния: `Busy`, `Degraded`, `Error`, `Disabled`.

## 4. События v0.1

- `KernelReady`;
- `KernelStartupFailed`;
- `UiStarted`;
- `KernelStopped`.

## 5. Метрики запуска

Kernel фиксирует:

- длительность запуска;
- количество сервисов;
- количество возможностей;
- успешность запуска.

## 6. Совместимость

Существующий `MainWindow` сохранён без изменения публичного поведения. Изменена только точка входа: интерфейс создаётся через `Bootstrap`.

## 7. Проверка

```powershell
python -m pip install -r requirements.txt
python -m pytest
python -m app.main
```

## 8. Ограничения v0.1

- Event Bus пока синхронный;
- реальные Platform Core сервисы будут регистрироваться в следующих этапах;
- восстановление после сбоя сервиса ещё не реализовано;
- Plugin Manager и асинхронный Startup Pipeline не входят в этот инкремент.

## 9. Следующий этап

KER-002 должен добавить Configuration Manager и Logging Manager как первые управляемые сервисы, зарегистрированные в Kernel.
