# Identity Core

## Purpose

Identity Core is the universal identity subsystem of DevHub. It defines stable contracts for identifier generation, persistence, registration, time access, metrics, and event publication.

## Status

Development. This branch contains the module skeleton and public contracts only.

## Architecture

The module follows DDD, Hexagonal Architecture, dependency inversion, explicit dependencies, and zero hidden global state.

Dependency direction:

```text
Domain <- Application <- Contracts <- Infrastructure
```

The domain layer must not import application or infrastructure code.

## Planned public API

- `generate`
- `parse`
- `validate`
- `describe`

The functions will be exported only after their implementations are available.

## License

See the repository root `LICENSE` file.
