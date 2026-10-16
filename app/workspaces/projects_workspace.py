"""Public GitHub project catalog; local Git repositories remain separate."""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QTextBrowser, QLineEdit, QComboBox


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
        except HTTPError as error:
            if error.code in (403, 429):
                self.failed.emit("GitHub временно ограничил число запросов. Повторите позже или настройте авторизацию.")
            elif error.code == 404:
                self.failed.emit("Профиль GitHub julcapp не найден.")
            else:
                self.failed.emit(f"GitHub вернул ошибку HTTP {error.code}.")
        except (URLError, TimeoutError) as error:
            self.failed.emit("Нет связи с GitHub. Проверьте интернет и повторите попытку.")
        except Exception as error:
            self.failed.emit(f"Ошибка обработки ответа GitHub: {error}")


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
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по названию, описанию и языку")
        self.search.textChanged.connect(self.filter_projects)
        layout.addWidget(self.search)
        self.kind_filter = QComboBox()
        self.kind_filter.addItems(["Все репозитории", "Собственные проекты", "Форки"])
        self.kind_filter.currentIndexChanged.connect(self.filter_projects)
        layout.addWidget(self.kind_filter)
        self.items = QListWidget()
        layout.addWidget(self.items)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(True)
        self.details.setMaximumHeight(190)
        layout.addWidget(self.details)
        self._projects = []
        self._visible_projects = []
        self.items.currentRowChanged.connect(self.show_project)
        self.status = QLabel("Подключение к GitHub…")
        layout.addWidget(self.status)
        self.reload()

    def reload(self) -> None:
        if self._thread is not None:
            return
        self.refresh.setEnabled(False)
        self.status.setText("Загрузка публичных репозиториев… Сохранённый список остаётся доступен.")
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
        self.filter_projects()


    @Slot()
    def filter_projects(self) -> None:
        query = self.search.text().strip().casefold()
        kind = self.kind_filter.currentIndex()
        self._visible_projects = [
            repo for repo in self._projects
            if (kind == 0 or bool(repo.get("fork")) == (kind == 2))
            and query in " ".join(str(repo.get(field) or "") for field in ("full_name", "description", "language")).casefold()
        ]
        self.items.clear()
        for repo in self._visible_projects:
            self.items.addItem(f"{'[Форк]' if repo.get('fork') else '[Проект]'} {repo.get('full_name', '')} — {repo.get('description') or 'Без описания'}")
        self.status.setText(f"Показано {len(self._visible_projects)} из {len(self._projects)} публичных репозиториев.")
        if self._visible_projects:
            self.items.setCurrentRow(0)
        else:
            self.details.clear()

    @Slot(int)
    def show_project(self, row: int) -> None:
        from html import escape
        if row < 0 or row >= len(self._visible_projects):
            self.details.clear()
            return
        repo = self._visible_projects[row]
        name = escape(repo.get("full_name") or "")
        description = escape(repo.get("description") or "Описание не указано")
        language = escape(repo.get("language") or "Не указан")
        url = repo.get("html_url") or ""
        safe_url = escape(url, quote=True) if url.startswith("https://github.com/") else ""
        link = '<a href="' + safe_url + '">Открыть на GitHub</a>' if safe_url else ""
        kind = "Форк стороннего проекта" if repo.get("fork") else "Собственный репозиторий"
        self.details.setHtml(f"<h3>{name}</h3><p>{description}</p><p>Тип: {kind}</p><p>Язык: {language}</p>{link}")

    @Slot(str)
    def failed(self, error: str) -> None:
        self.status.setText(f"Не удалось обновить проекты: {error} Ранее загруженные данные сохранены.")

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
