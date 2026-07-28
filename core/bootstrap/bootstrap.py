"""Официальная точка сборки и запуска DevHub."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.events.event_bus import Event
from core.kernel.kernel import Kernel

WindowFactory = Callable[[], Any]


class Bootstrap:
    """Запускает Kernel и передаёт управление существующему UI."""

    def __init__(self, window_factory: WindowFactory) -> None:
        self._window_factory = window_factory
        self.kernel = Kernel()
        self.window: Any | None = None

    def run(self) -> Any:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        logger = logging.getLogger("devhub.bootstrap")

        metrics = self.kernel.start()
        logger.info(
            "Kernel Ready: version=%s services=%d capabilities=%d startup=%.4fs",
            self.kernel.version,
            metrics.services,
            metrics.capabilities,
            metrics.startup_seconds,
        )

        self.window = self._window_factory()
        self.kernel.events.publish(Event("UiStarted", source="bootstrap"))
        return self.window

    def shutdown(self) -> None:
        self.kernel.shutdown()
