from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from app.workspaces.explorer.controller import FilePreview


class DocumentViewer(QWidget):
    """Просмотр поддерживаемых текстовых файлов проекта."""

    def __init__(self) -> None:
        super().__init__()
        self.title = QLabel("Выберите файл в дереве проекта")
        self.title.setObjectName("PanelTitle")
        self.meta = QLabel("")
        self.meta.setWordWrap(True)
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addWidget(self.editor, 1)

    def clear_preview(self, message: str = "Выберите файл в дереве проекта") -> None:
        self.title.setText(message)
        self.meta.clear()
        self.editor.clear()

    def show_preview(self, preview: FilePreview) -> None:
        self.title.setText(preview.path.name)
        self.meta.setText(
            f"Тип: {preview.kind}  •  Размер: {preview.size_bytes} байт  •  "
            f"Строк: {preview.line_count}\n{preview.path}"
        )
        self.editor.setPlainText(preview.content)
