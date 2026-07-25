# Changelog

All notable changes to Identity Core will be documented in this file.

## [Unreleased]

### Added
- Initial module skeleton.
- Public contracts for strategies, providers, registry, clock, metrics, and events.
- Immutable domain model: `EntityId`, `EntityType`, and `IdentityDescriptor`.
- Identity Core exception hierarchy and pure validators.
- Thread-safe `SequentialStrategy` with independent counters per entity type.
- Thread-safe `InMemoryProvider` with collision detection.
- Registry, system clock, and application service orchestration.
- Lazy bootstrap composition root with service override support.
- Frozen public facade: `generate`, `parse`, `validate`, and `describe`.
- Domain, architecture, contract, infrastructure, service, and facade tests.
- Module manifest and module documentation.
