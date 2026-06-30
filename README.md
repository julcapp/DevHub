# DevHub

**DevHub — ваш центр управления инженерными проектами.**

DevHub — настольная инженерная платформа для управления проектами, репозиториями Git, документацией, метаданными DHMS, рекомендациями DevAdvisor и жизненным циклом разработки.

## Назначение

DevHub помогает создателю проекта, разработчику или руководителю инженерной разработки держать под контролем несколько проектов одновременно.

Платформа объединяет:

- реестр локальных Git-репозиториев;
- синхронизацию с GitHub;
- паспорт проекта;
- анализ состояния проекта;
- рекомендации DevAdvisor;
- контроль README, DHMS, документации и структуры проекта;
- будущие модули автоматизации, идей, интеллектуальной собственности и коммерческой лицензии.

## Текущая версия

```text
DevHub v0.4 Alpha
```

## Основные возможности v0.4 Alpha

- поиск локальных Git-репозиториев;
- отображение ветки проекта;
- отображение состояния синхронизации;
- отображение даты последнего локального commit;
- отображение даты последнего commit на GitHub;
- выполнение Fetch, Pull, Push для выбранного проекта;
- синхронизация всех проектов;
- чтение `.devhub/project.json`;
- отображение паспорта проекта;
- первичный анализ DevAdvisor;
- проверка README, DHMS, docs, CHANGELOG;
- журнал операций.

## Структура проекта

```text
DevHub
│
├── app
│   ├── main.py
│   ├── ui.py
│   ├── git_manager.py
│   ├── project_metadata.py
│   └── devadvisor.py
│
├── config
│   └── settings.json
│
├── docs
│   ├── 01_Requirements
│   ├── 02_Architecture
│   └── 14_Language
│
├── logs
├── plugins
├── tests
├── .devhub
│   └── project.json
│
├── README.md
├── CHANGELOG.md
├── LICENSE
└── requirements.txt
```

## Основные модули

### Git Manager

Отвечает за работу с локальными Git-репозиториями:

- поиск репозиториев;
- определение ветки;
- Fetch;
- Pull;
- Push;
- определение состояния синхронизации;
- проверка локальных изменений.

### Project Metadata

Отвечает за чтение паспорта проекта из:

```text
.devhub/project.json
```

Если паспорт проекта отсутствует, DevHub использует базовые данные из репозитория.

### DevAdvisor

DevAdvisor — интеллектуальный инженерный помощник DevHub.

В текущей версии он проверяет:

- наличие README;
- заполненность README;
- наличие `.devhub/project.json`;
- наличие папки `docs`;
- наличие `CHANGELOG.md`;
- базовую инженерную полноту проекта.

В будущих версиях DevAdvisor будет анализировать:

- архитектуру;
- документацию;
- RoadMap;
- ADR;
- технический долг;
- DevScore;
- готовность к релизу;
- идеи и интеллектуальные активы.

## Установка зависимостей

```powershell
cd "C:\Users\iav\Documents\GitHub\DevHub"
python -m pip install -r requirements.txt
```

Если `requirements.txt` пустой, минимально установите:

```powershell
python -m pip install PySide6
```

## Запуск из исходников

```powershell
cd "C:\Users\iav\Documents\GitHub\DevHub"
python -m app.main
```

## Сборка EXE

```powershell
python -m PyInstaller --onefile --windowed --name DevHub app\main.py
```

После сборки файл будет находиться в:

```text
dist\DevHub.exe
```

## Настройки

Основной файл настроек:

```text
config/settings.json
```

Пример:

```json
{
  "workspace_paths": [
    "C:\\Users\\iav\\Documents\\GitHub"
  ],
  "default_branch": "main",
  "allowed_branches": [
    "main",
    "master"
  ],
  "exclude_folders": [],
  "theme": "light"
}
```

## DHMS

DevHub использует стандарт DHMS — DevHub Metadata Specification.

Каждый проект должен содержать:

```text
.devhub/project.json
```

Этот файл является паспортом проекта и основным источником структурированных данных для DevHub.

## Язык интерфейса

Пользовательский интерфейс DevHub по умолчанию должен быть на русском языке.

Название **DevAdvisor** не переводится, так как является частью бренда продукта.

Терминология интерфейса фиксируется в документе:

```text
docs/14_Language/DLS-0001.md
```

## Стратегическое направление

DevHub развивается как платформа управления жизненным циклом инженерных проектов.

Ключевые будущие направления:

- DevAdvisor;
- Automation Center;
- Innovation Hub;
- Idea Vault;
- IP Center;
- Environment Manager;
- Lifecycle Manager;
- Project Health;
- DevScore;
- DevHub Pro;
- Marketplace.

## Статус проекта

```text
Alpha / активная разработка
```

