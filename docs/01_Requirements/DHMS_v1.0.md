# DevHub Metadata Specification (DHMS)

**Document ID:** DHMS-001  
**Version:** 1.0.0  
**Status:** Approved  
**Author:** DevHub Project  
**Date:** 2026-06-29

---

# 1. Назначение

DevHub Metadata Specification (DHMS) определяет единый стандарт хранения структурированной информации о проектах.

Цель стандарта:

- единообразное описание проектов;
- автоматическое обнаружение проектов DevHub;
- поддержка аналитики;
- поддержка AI-модулей;
- автоматическое построение панели управления.

README.md предназначен исключительно для человека.

Все служебные данные должны храниться в каталоге `.devhub`.

---

# 2. Структура проекта

Каждый проект должен содержать каталог

.devhub/

Минимальная структура:

.devhub/
    project.json

Рекомендуемая структура:

.devhub/
    project.json
    roadmap.json
    releases.json
    metrics.json
    ai.json

---

# 3. project.json

Минимальная схема

```json
{
  "name": "",
  "code": "",
  "version": "",
  "owner": "",
  "status": "",
  "priority": "",
  "type": "",
  "description": "",
  "repository": "",
  "default_branch": "main",
  "language": "",
  "framework": "",
  "created": "",
  "updated": "",
  "documentation": "",
  "homepage": "",
  "license": "",
  "tags": [],
  "modules": []
}
```

---

# 4. Допустимые значения

## Status

- development
- testing
- release
- production
- maintenance
- archived

## Priority

- critical
- high
- normal
- low

## Type

- desktop
- web
- api
- service
- library
- documentation
- automation
- mobile

---

# 5. Правила

1. Каждый репозиторий должен содержать каталог `.devhub`.

2. DevHub читает данные только из `.devhub/project.json`.

3. README.md используется исключительно как документация для разработчиков и пользователей.

4. Все проекты экосистемы должны соответствовать DHMS.

---

# 6. Совместимость

Версия DHMS должна храниться внутри `project.json`.

Это позволит DevHub поддерживать несколько поколений стандарта.

---

# 7. Будущее развитие

Планируется расширение стандарта:

- roadmap.json
- releases.json
- metrics.json
- ai.json
- security.json
- quality.json

---

Конец документа.