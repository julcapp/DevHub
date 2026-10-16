"""Public GitHub project catalog; local Git repositories remain separate."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QTextBrowser


class ProjectLoader(QObject):
    finished = Signal(object)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        try:
            projects = []
            for page in range(1, 11):
                url = f"https://api.github.com/users/julcapp/repos?per_page=100&page={page}&sort=updated"
                request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "DevHub"})
                with urlopen(request, timeout=15) as response:
                    batch = json.load(response)
                if not isinstance(batch, list):
                    raise ValueError("Неожиданный ответ GitHub")
                projects.extend(batch)
                if len(batch) < 100:
                    break
            self.finished.emit(projects)
        except Exception as error:
            self.failed.emit(str(error))


class ProjectsWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._thread = None
        self._worker = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Мои проекты GitHub — julcapp"))
        layout.addWidget(QLabel("Публичные репозитории GitHub. Локальные проекты доступны в разделе «Разработка»."))
        self.refresh = QPushButton("Обновить проекты из GitHub")
        self.refresh.clicked.connect(self.reload)
        layout.addWidget(self.refresh)
        self.items = QListWidget()
        layout.addWidget(self.items)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(True)
        self.details.setMaximumHeight(190)
        layout.addWidget(self.details)
        self._projects = []
        self.items.currentRowChanged.connect(self.show_project)
        self.status = QLabel("Подключение к GitHub…")
        layout.addWidget(self.status)
        self.reload()

    def reload(self) -> None:
        if self._thread is not None:
            return
        self.refresh.setEnabled(False)
        self.status.setText("Загрузка публичных репозиториев…")
        thread = QThread(self)
        worker = ProjectLoader()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self.loaded)
        worker.failed.connect(self.failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self.cleanup)
        thread.finished.connect(thread.deleteLater)
        self._thread, self._worker = thread, worker
        thread.start()

    @Slot(object)
    def loaded(self, projects: object) -> None:
        self._projects = projects
        self.items.clear()
        for repo in projects:
            self.items.addItem(f"{repo.get('full_name', '')} — {repo.get('description') or 'Без описания'}")
        self.status.setText(f"Загружено публичных репозиториев: {len(projects)}.")
        if projects:
            self.items.setCurrentRow(0)

    @Slot(int)
    def show_project(self, row: int) -> None:
        from html import escape
        if row < 0 or row >= len(self._projects):
            self.details.clear()
            return
        repo = self._projects[row]
        name = escape(repo.get("full_name") or "")
        description = escape(repo.get("description") or "Описание не указано")
        language = escape(repo.get("language") or "Не указан")
        url = repo.get("html_url") or ""
        safe_url = escape(url, quote=True) if url.startswith("https://github.com/") else ""
        link = '<a href="' + safe_url + '">Открыть на GitHub</a>' if safe_url else ""
        self.details.setHtml(f"<h3>{name}</h3><p>{description}</p><p>Язык: {language}</p>{link}")

    @Slot(str)
    def failed(self, error: str) -> None:
        self.status.setText(f"Не удалось загрузить проекты: {error}")

    @Slot()
    def cleanup(self) -> None:
        self._thread, self._worker = None, None
        self.refresh.setEnabled(True)

    def closeEvent(self, event) -> None:
        if self._thread is not None and self._thread.isRunning():
            self.status.setText("Ожидаем завершения загрузки…")
            event.ignore()
            return
        super().closeEvent(event)
