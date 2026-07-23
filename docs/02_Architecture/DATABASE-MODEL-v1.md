# DevHub Database Model v1

Статус: Draft for implementation  
Связано: ADR-001, ADR-002, CORE-MODEL-v1, Issue #2

## 1. Цель

Зафиксировать физическую PostgreSQL-модель для инженерных объектов DevHub, графа связей, GitHub Stars, исследований и происхождения производных проектов.

## 2. Базовые принципы

1. Каждый доменный объект имеет запись в `engineering_objects`.
2. Специализированные таблицы используют тот же UUID как PK и FK.
3. Публичный идентификатор EO стабилен и не зависит от имени, пути или GitHub URL.
4. Связи хранятся в `object_relations` как ориентированный граф.
5. История происхождения не удаляется каскадно.
6. GitHub-синхронизация не перезаписывает пользовательские заметки и решения.
7. AI-анализ версионируется и не считается пользовательским решением.

## 3. Схемы PostgreSQL

- `core` — Engineering Objects, связи, аудит.
- `projects` — продукты и репозитории.
- `research` — Stars, исследования, идеи, технологии, эволюция.
- `ai` — версии AI-анализа.

## 4. Таблицы

### core.engineering_objects

- `id uuid primary key`
- `eo_id varchar(32) unique not null`
- `object_type varchar(32) not null`
- `title varchar(300) not null`
- `description text`
- `status varchar(32) not null default 'draft'`
- `author_id uuid`
- `source_type varchar(32)`
- `source_ref text`
- `version integer not null default 1`
- `metadata jsonb not null default '{}'`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`
- `archived_at timestamptz`

Ограничение: `object_type` только из утверждённого каталога типов.

### core.object_relations

- `id uuid primary key`
- `source_object_id uuid not null`
- `target_object_id uuid not null`
- `relation_type varchar(48) not null`
- `properties jsonb not null default '{}'`
- `created_by uuid`
- `created_at timestamptz not null`
- unique (`source_object_id`, `target_object_id`, `relation_type`)

Удаление объектов не должно физически удалять происхождение; применяется архивирование.

### core.audit_events

- `id bigserial primary key`
- `object_id uuid`
- `event_type varchar(64) not null`
- `actor_type varchar(24) not null`
- `actor_id uuid`
- `payload jsonb not null default '{}'`
- `occurred_at timestamptz not null`

### projects.projects

- `id uuid primary key references core.engineering_objects(id)`
- `project_code varchar(64) unique`
- `project_type varchar(32)`
- `primary_repository_id uuid`
- `commercial_status varchar(32)`
- `roadmap_ref text`

### projects.repositories

- `id uuid primary key references core.engineering_objects(id)`
- `provider varchar(24) not null default 'github'`
- `provider_repository_id bigint`
- `owner varchar(255)`
- `name varchar(255)`
- `html_url text`
- `clone_url text`
- `local_path text`
- `default_branch varchar(255)`
- `license_spdx varchar(64)`
- `fork boolean not null default false`
- `parent_repository_id uuid`
- `upstream_repository_id uuid`
- `last_synced_at timestamptz`
- unique (`provider`, `provider_repository_id`)

### research.github_stars

- `id uuid primary key references core.engineering_objects(id)`
- `repository_id uuid not null`
- `github_user_id bigint not null`
- `starred_at timestamptz`
- `imported_at timestamptz not null`
- `research_status varchar(32) not null default 'unreviewed'`
- `user_priority smallint`
- `user_notes text`
- `decision varchar(32)`
- `decision_reason text`
- unique (`github_user_id`, `repository_id`)

### research.ideas

- `id uuid primary key references core.engineering_objects(id)`
- `problem_statement text`
- `expected_value text`
- `maturity varchar(32)`
- `priority smallint`
- `confidentiality varchar(24) not null default 'private'`

### research.research_items

- `id uuid primary key references core.engineering_objects(id)`
- `source_star_id uuid`
- `research_question text not null`
- `hypothesis text`
- `conclusion text`
- `recommendation varchar(32)`
- `next_action varchar(64)`
- `started_at timestamptz`
- `completed_at timestamptz`

### research.technologies

- `id uuid primary key references core.engineering_objects(id)`
- `category varchar(64)`
- `current_version varchar(64)`
- `website_url text`
- `license_spdx varchar(64)`
- `maturity_score numeric(5,2)`

### research.evolution_nodes

- `id uuid primary key references core.engineering_objects(id)`
- `project_id uuid`
- `repository_id uuid`
- `origin_repository_id uuid`
- `origin_star_id uuid`
- `generation integer not null default 0`
- `derivation_type varchar(32)`
- `license_snapshot jsonb not null default '{}'`
- `created_from_commit varchar(64)`

### ai.analysis_versions

- `id uuid primary key`
- `object_id uuid not null`
- `analysis_type varchar(48) not null`
- `model_provider varchar(32)`
- `model_name varchar(128)`
- `prompt_version varchar(32)`
- `result jsonb not null`
- `score numeric(5,2)`
- `created_at timestamptz not null`
- `supersedes_id uuid`

## 5. Ключевые индексы

- GIN по `engineering_objects.metadata`.
- B-tree по `engineering_objects.object_type`, `status`, `updated_at`.
- B-tree по обоим концам `object_relations`.
- GIN/tsvector для полнотекстового поиска по title, description, notes, conclusion.
- Индекс по `repositories.provider_repository_id`.
- Индекс по `github_stars.research_status`, `decision`, `user_priority`.

## 6. EO-ID

Формат:

`EO-{TYPE}-{SEQUENCE}`

Примеры:

- `EO-PROJ-000125`
- `EO-STAR-000021`
- `EO-IDEA-000078`
- `EO-RES-000009`

Внутренний PK остаётся UUID. EO-ID создаётся сервером через отдельную последовательность по типу объекта.

## 7. Правила удаления

- Физическое удаление запрещено для объектов с отношениями происхождения.
- Пользовательское удаление переводит объект в `archived`.
- `object_relations`, `audit_events`, `evolution_nodes` сохраняются.
- Допускается hard delete только для ошибочно импортированных объектов без зависимостей и до пользовательского решения.

## 8. Транзакционные границы

Создание производного проекта выполняется одной прикладной транзакцией:

1. создать Repository EO;
2. создать Project EO;
3. создать EvolutionNode;
4. связать Star → Research → Repository → Project;
5. сохранить снимок лицензии;
6. записать audit events.

GitHub Fork и Clone являются внешними операциями и управляются через saga/outbox, а не внутри SQL-транзакции.
