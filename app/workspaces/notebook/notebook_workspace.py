from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.workspaces.notebook.controller import (
    NOTEBOOK_CATEGORIES,
    EngineeringNotebookController,
)


class TranscriptionWorker(QThread):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, audio_path: Path) -> None:
        super().__init__()
        self.audio_path = audio_path

    def run(self) -> None:
        try:
            from app.workspaces.notebook.offline_speech import (
                OfflineSpeechRecognizer, default_model_dir,
            )
            text = OfflineSpeechRecognizer(default_model_dir()).transcribe_file(self.audio_path)
            self.completed.emit(text)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.audio_path.unlink(missing_ok=True)


class EngineeringNotebookWorkspace(QWidget):
    """Инженерный журнал проекта: идеи, ADR, решения, задачи и исследования."""

    def __init__(self) -> None:
        super().__init__()
        self.controller = EngineeringNotebookController()
        self._recorder = None
        self._transcription_worker = None
        self._transcription_document = None
        self._transcription_generation = 0
        self.current_document: Path | None = None
        self._loading_document = False
        self._saved_content = ""
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(1200)
        self._autosave_timer.timeout.connect(self._autosave_document)
        self.project_label = QLabel("Проект не выбран")
        self.categories = QListWidget()
        self.documents = QListWidget()
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Выберите или создайте документ")
        self.save_button = QPushButton("Сохранить")
        self.record_button = QPushButton("🎤 Записать заметку")
        self.record_button.clicked.connect(self.toggle_local_recording)
        self.dictation_button = QPushButton("🎙 Handy")
        self.dictation_button.setToolTip("Начать или остановить запись в установленном Handy. Текст вставляется в редактор автоматически.")
        self.dictation_button.clicked.connect(self.toggle_dictation)
        self.delete_button = QPushButton("Удалить")
        self._build_ui()
        self._populate_categories()
        self.categories.currentTextChanged.connect(self._change_category)
        self.documents.itemSelectionChanged.connect(self._open_selected_document)
        self.save_button.clicked.connect(self.save_current_document)
        self.editor.textChanged.connect(self._schedule_autosave)
        self.delete_button.clicked.connect(self.delete_current_document)
        self._update_controls()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Инженерный журнал")
        title.setObjectName("WorkspaceTitle")
        choose_button = QPushButton("Открыть проект")
        choose_button.clicked.connect(self.choose_project)
        new_button = QPushButton("Новый документ")
        new_button.clicked.connect(self.create_document)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(choose_button)
        header.addWidget(new_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        category_panel = QWidget()
        category_layout = QVBoxLayout(category_panel)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.addWidget(self.project_label)
        category_layout.addWidget(QLabel("Разделы"))
        category_layout.addWidget(self.categories, 1)

        document_panel = QWidget()
        document_layout = QVBoxLayout(document_panel)
        document_layout.setContentsMargins(0, 0, 0, 0)
        document_layout.addWidget(QLabel("Документы"))
        document_layout.addWidget(self.documents, 1)

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(QLabel("Редактор Markdown"))
        editor_layout.addWidget(self.editor, 1)
        self.save_status = QLabel("Все изменения сохраняются автоматически")
        editor_layout.addWidget(self.save_status)
        editor_actions = QHBoxLayout()
        editor_actions.addStretch()
        editor_actions.addWidget(self.record_button)
        editor_actions.addWidget(self.dictation_button)
        editor_actions.addWidget(self.delete_button)
        editor_actions.addWidget(self.save_button)
        editor_layout.addLayout(editor_actions)

        splitter.addWidget(category_panel)
        splitter.addWidget(document_panel)
        splitter.addWidget(editor_panel)
        splitter.setSizes([220, 320, 760])

        layout.addLayout(header)
        layout.addWidget(splitter, 1)

    def toggle_local_recording(self) -> None:
        from app.workspaces.notebook.microphone import MicrophoneRecorder
        if self._recorder is None:
            recorder = MicrophoneRecorder()
            try:
                recorder.start()
            except Exception as error:
                QMessageBox.warning(self, "Голосовые заметки", str(error))
                return
            self._recorder = recorder
            self.record_button.setText("⏹ Остановить запись")
            self.save_status.setText("Идёт запись с микрофона…")
            return
        recorder = self._recorder
        self._recorder = None
        self.record_button.setText("🎤 Записать заметку")
        try:
            path = recorder.stop()
        except Exception as error:
            QMessageBox.warning(self, "Голосовые заметки", str(error))
            return
        self.record_button.setEnabled(False)
        self._transcription_document = self.current_document
        self._transcription_generation += 1
        self.save_status.setText("Распознавание речи…")
        worker = TranscriptionWorker(path)
        self._transcription_worker = worker
        worker.completed.connect(self._insert_transcription)
        worker.failed.connect(self._transcription_failed)
        worker.finished.connect(self._transcription_finished)
        worker.start()

    def _insert_transcription(self, text: str) -> None:
        if self.current_document is None or self.current_document != self._transcription_document:
            return
        if text:
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText("\n" + text + "\n")
            self.editor.setTextCursor(cursor)

    def _transcription_failed(self, message: str) -> None:
        QMessageBox.warning(self, "Голосовые заметки", message)

    def _transcription_finished(self) -> None:
        self._transcription_worker = None
        self._transcription_document = None
        self._update_controls()

    def toggle_dictation(self) -> None:
        """Trigger the separately installed Handy application; never capture audio in DevHub."""
        command = self._find_handy()
        if command is None:
            QMessageBox.information(
                self,
                "Голосовые заметки",
                "Handy не найден в PATH. Установите его с https://github.com/cjpais/Handy/releases, "
                "запустите, настройте микрофон и модель, затем повторите. "
                "Также можно диктовать глобальным сочетанием клавиш Handy прямо в редактор.",
            )
            return
        self.editor.setFocus()
        try:
            subprocess.Popen([command, "--toggle-transcription"], close_fds=True)
        except OSError as error:
            QMessageBox.warning(self, "Голосовые заметки", f"Не удалось запустить Handy: {error}")

    @staticmethod
    def _find_handy() -> str | None:
        command = shutil.which("handy") or shutil.which("Handy.exe")
        if command:
            return command
        if os.name == "nt":
            candidates = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Handy" / "Handy.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Handy" / "Handy.exe",
                Path(os.environ.get("PROGRAMFILES", "")) / "Handy" / "Handy.exe",
            ]
            for candidate in candidates:
                if candidate.is_file():
                    return str(candidate)
        return None

    def _schedule_autosave(self) -> None:
        if self._loading_document or self.current_document is None:
            return
        if self.editor.toPlainText() != self._saved_content:
            self.save_status.setText("Есть несохранённые изменения…")
            self._autosave_timer.start()
        else:
            self._autosave_timer.stop()
            self.save_status.setText("Все изменения сохранены")

    def _autosave_document(self) -> None:
        if self.current_document is not None and self.editor.toPlainText() != self._saved_content:
            self.save_current_document()

    def _flush_pending_changes(self) -> bool:
        self._autosave_timer.stop()
        if self.current_document is None or self.editor.toPlainText() == self._saved_content:
            return True
        return self.save_current_document()

    def _populate_categories(self) -> None:
        self.categories.clear()
        for title in NOTEBOOK_CATEGORIES:
            self.categories.addItem(title)
        self.categories.setCurrentRow(0)

    def choose_project(self) -> None:
        if not self._flush_pending_changes():
            return
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if directory:
            self.set_project(Path(directory))

    def set_project(self, project_root: Path) -> None:
        if not self._flush_pending_changes():
            return
        try:
            self.controller.set_project(project_root)
        except ValueError as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self.project_label.setText(str(project_root.resolve()))
        self.current_document = None
        self._saved_content = ""
        self.editor.clear()
        self._reload_documents(self.categories.currentItem().text() if self.categories.currentItem() else "Идеи")
        self._update_controls()

    def create_document(self) -> None:
        if not self._flush_pending_changes():
            return
        if self.controller.project_root is None:
            QMessageBox.information(self, "Engineering Notebook", "Сначала выберите проект")
            return
        category = self.categories.currentItem().text() if self.categories.currentItem() else "Идеи"
        title, accepted = QInputDialog.getText(self, "Новый документ", "Название:")
        if not accepted:
            return
        try:
            document = self.controller.create_document(category, title)
        except (RuntimeError, ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self._reload_documents(category)
        self._select_document(document.path)

    def save_current_document(self) -> bool:
        if self.current_document is None:
            return True
        try:
            self.controller.save_document(self.current_document, self.editor.toPlainText())
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            self.save_status.setText("Не удалось сохранить изменения")
            return False
        self._saved_content = self.editor.toPlainText()
        self.save_status.setText("Все изменения сохранены")
        self._reload_documents(self.categories.currentItem().text() if self.categories.currentItem() else "Идеи")
        self._select_document(self.current_document)
        return True

    def delete_current_document(self) -> None:
        self._autosave_timer.stop()
        if self.current_document is None:
            return
        answer = QMessageBox.question(
            self,
            "Удаление документа",
            f"Удалить {self.current_document.name}?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.delete_document(self.current_document)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self.current_document = None
        self._saved_content = ""
        self.editor.clear()
        self._reload_documents(self.categories.currentItem().text() if self.categories.currentItem() else "Идеи")
        self._update_controls()

    def _change_category(self, category: str) -> None:
        if not self._flush_pending_changes():
            return
        self.current_document = None
        self._saved_content = ""
        self.editor.clear()
        self._reload_documents(category)
        self._update_controls()

    def _reload_documents(self, category: str) -> None:
        self.documents.clear()
        if self.controller.project_root is None:
            return
        try:
            paths = self.controller.list_documents(category)
        except (RuntimeError, ValueError, OSError):
            return
        for path in paths:
            item = QListWidgetItem(path.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.documents.addItem(item)

    def _open_selected_document(self) -> None:
        if not self._flush_pending_changes():
            return
        item = self.documents.currentItem()
        if item is None:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        try:
            document = self.controller.load_document(path)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Engineering Notebook", str(error))
            return
        self._loading_document = True
        self.current_document = document.path
        self._saved_content = document.content
        self.editor.setPlainText(document.content)
        self._loading_document = False
        self.save_status.setText("Все изменения сохранены")
        self._update_controls()

    def _select_document(self, path: Path) -> None:
        for index in range(self.documents.count()):
            item = self.documents.item(index)
            if Path(item.data(Qt.ItemDataRole.UserRole)) == path:
                self.documents.setCurrentItem(item)
                return

    def _update_controls(self) -> None:
        enabled = self.current_document is not None
        self.editor.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        self.dictation_button.setEnabled(enabled)
        self.record_button.setEnabled(enabled and self._transcription_worker is None)

    def closeEvent(self, event) -> None:
        if self._recorder is not None:
            self._recorder.cancel()
            self._recorder = None
        if self._transcription_worker is not None and self._transcription_worker.isRunning():
            event.ignore()
            return
        if not self._flush_pending_changes():
            event.ignore()
            return
        super().closeEvent(event)
