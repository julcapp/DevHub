# DevHub ER Diagram v1

Статус: Draft for implementation  
Связано: DATABASE-MODEL-v1, ADR-001, ADR-002

```mermaid
erDiagram
    ENGINEERING_OBJECTS ||--o| PROJECTS : specializes
    ENGINEERING_OBJECTS ||--o| REPOSITORIES : specializes
    ENGINEERING_OBJECTS ||--o| GITHUB_STARS : specializes
    ENGINEERING_OBJECTS ||--o| IDEAS : specializes
    ENGINEERING_OBJECTS ||--o| RESEARCH_ITEMS : specializes
    ENGINEERING_OBJECTS ||--o| TECHNOLOGIES : specializes
    ENGINEERING_OBJECTS ||--o| EVOLUTION_NODES : specializes

    ENGINEERING_OBJECTS ||--o{ OBJECT_RELATIONS : source
    ENGINEERING_OBJECTS ||--o{ OBJECT_RELATIONS : target
    ENGINEERING_OBJECTS ||--o{ AUDIT_EVENTS : records
    ENGINEERING_OBJECTS ||--o{ ANALYSIS_VERSIONS : analyzed

    REPOSITORIES ||--o{ GITHUB_STARS : starred_repository
    GITHUB_STARS ||--o{ RESEARCH_ITEMS : initiates
    REPOSITORIES ||--o{ REPOSITORIES : parent_or_upstream
    PROJECTS }o--o| REPOSITORIES : primary_repository

    PROJECTS ||--o{ EVOLUTION_NODES : evolves
    REPOSITORIES ||--o{ EVOLUTION_NODES : implementation
    GITHUB_STARS ||--o{ EVOLUTION_NODES : origin_star
    REPOSITORIES ||--o{ EVOLUTION_NODES : origin_repository

    ENGINEERING_OBJECTS {
        uuid id PK
        varchar eo_id UK
        varchar object_type
        varchar title
        varchar status
        jsonb metadata
        timestamptz created_at
        timestamptz archived_at
    }

    OBJECT_RELATIONS {
        uuid id PK
        uuid source_object_id FK
        uuid target_object_id FK
        varchar relation_type
        jsonb properties
        timestamptz created_at
    }

    PROJECTS {
        uuid id PK_FK
        varchar project_code UK
        varchar project_type
        uuid primary_repository_id FK
        varchar commercial_status
    }

    REPOSITORIES {
        uuid id PK_FK
        varchar provider
        bigint provider_repository_id
        varchar owner
        varchar name
        text html_url
        varchar license_spdx
        boolean fork
        uuid parent_repository_id FK
        uuid upstream_repository_id FK
    }

    GITHUB_STARS {
        uuid id PK_FK
        uuid repository_id FK
        bigint github_user_id
        timestamptz starred_at
        varchar research_status
        smallint user_priority
        text user_notes
        varchar decision
    }

    IDEAS {
        uuid id PK_FK
        text problem_statement
        text expected_value
        varchar maturity
        smallint priority
        varchar confidentiality
    }

    RESEARCH_ITEMS {
        uuid id PK_FK
        uuid source_star_id FK
        text research_question
        text hypothesis
        text conclusion
        varchar recommendation
        varchar next_action
    }

    TECHNOLOGIES {
        uuid id PK_FK
        varchar category
        varchar current_version
        varchar license_spdx
        numeric maturity_score
    }

    EVOLUTION_NODES {
        uuid id PK_FK
        uuid project_id FK
        uuid repository_id FK
        uuid origin_repository_id FK
        uuid origin_star_id FK
        integer generation
        varchar derivation_type
        jsonb license_snapshot
        varchar created_from_commit
    }

    ANALYSIS_VERSIONS {
        uuid id PK
        uuid object_id FK
        varchar analysis_type
        varchar model_name
        varchar prompt_version
        jsonb result
        numeric score
        uuid supersedes_id FK
    }

    AUDIT_EVENTS {
        bigint id PK
        uuid object_id FK
        varchar event_type
        varchar actor_type
        jsonb payload
        timestamptz occurred_at
    }
```

## Основные маршруты трассируемости

### Из GitHub Star в собственный продукт

`GitHubStar → ResearchItem → Decision → Repository(Fork) → Project → EvolutionNode`

### Из идеи в реализацию

`Idea → ResearchItem → Technology → ADR → Project → Repository`

### Обновление upstream

`Origin Repository → Upstream Snapshot → Compatibility Analysis → Merge Decision → Derivative Repository`

## Типы отношений первой версии

- `BASED_ON`
- `INSPIRED_BY`
- `IMPLEMENTS`
- `USES_TECHNOLOGY`
- `RESEARCHES`
- `DERIVED_FROM`
- `FORK_OF`
- `UPSTREAM_OF`
- `DOCUMENTS`
- `DECIDED_BY`
- `SUPERSEDES`
- `RELATED_TO`

Типы должны храниться в справочнике или контролироваться приложением; произвольные строки из UI не допускаются.
