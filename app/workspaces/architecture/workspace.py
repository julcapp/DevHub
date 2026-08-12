from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog,QGridLayout,QHBoxLayout,QLabel,QListWidget,QPushButton,QSplitter,QTextEdit,QVBoxLayout,QWidget
from app.workspaces.architecture.controller import ArchitectureSummary,ArchitectureWorkspaceController
from app.workspaces.architecture.graph_view import ArchitectureGraphView

class ArchitectureWorkspace(QWidget):
    """Центр архитектуры: сводка, интерактивная карта, модули и предупреждения."""
    def __init__(self)->None:
        super().__init__(); self.controller=ArchitectureWorkspaceController(); self.root_path:Path|None=None; self.summary:ArchitectureSummary|None=None
        self.project_label=QLabel("Проект не выбран"); self.status_label=QLabel("Выберите локальный проект и запустите анализ.")
        self.dependencies=QListWidget(); self.warnings=QListWidget(); self.modules=QListWidget(); self.module_details=QTextEdit(); self.module_details.setReadOnly(True); self.graph_view=ArchitectureGraphView(); self.metrics:dict[str,QLabel]={}; self._build_ui()
    def _build_ui(self)->None:
        layout=QVBoxLayout(self); header=QHBoxLayout(); title=QLabel("Центр архитектуры"); title.setObjectName("WorkspaceTitle")
        choose=QPushButton("Выбрать проект"); choose.clicked.connect(self.choose_project); analyze=QPushButton("Анализировать"); analyze.clicked.connect(self.analyze)
        header.addWidget(title); header.addStretch(); header.addWidget(choose); header.addWidget(analyze); layout.addLayout(header); layout.addWidget(self.project_label); layout.addWidget(self.status_label)
        grid=QGridLayout(); names=[("files","Файлы"),("folders","Папки"),("modules","Модули"),("classes","Классы"),("methods","Методы"),("functions","Функции"),("imports","Импорты"),("internal_dependencies","Внутренние зависимости"),("nodes_total","Узлы графа"),("edges_total","Связи графа")]
        for i,(key,text) in enumerate(names):
            value=QLabel("—"); value.setObjectName("ArchitectureMetric"); self.metrics[key]=value; row,col=i//2,(i%2)*2; grid.addWidget(QLabel(text),row,col); grid.addWidget(value,row,col+1)
        layout.addLayout(grid); layout.addWidget(QLabel("Карта модулей")); layout.addWidget(self.graph_view,2)
        splitter=QSplitter(Qt.Orientation.Horizontal); left=QWidget(); ll=QVBoxLayout(left); ll.setContentsMargins(0,0,0,0); ll.addWidget(QLabel("Модули проекта")); ll.addWidget(self.modules); right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.addWidget(QLabel("Карточка модуля")); rl.addWidget(self.module_details); splitter.addWidget(left); splitter.addWidget(right); layout.addWidget(splitter,2)
        bottom=QSplitter(Qt.Orientation.Horizontal); db=QWidget(); dl=QVBoxLayout(db); dl.setContentsMargins(0,0,0,0); dl.addWidget(QLabel("Все зависимости модулей")); dl.addWidget(self.dependencies); wb=QWidget(); wl=QVBoxLayout(wb); wl.setContentsMargins(0,0,0,0); wl.addWidget(QLabel("Архитектурные предупреждения")); wl.addWidget(self.warnings); bottom.addWidget(db); bottom.addWidget(wb); layout.addWidget(bottom,1)
        self.modules.currentRowChanged.connect(self._show_module); self.graph_view.module_selected.connect(self._select_module_by_name)
    def choose_project(self)->None:
        directory=QFileDialog.getExistingDirectory(self,"Выберите папку проекта")
        if directory: self.root_path=Path(directory); self.project_label.setText(str(self.root_path)); self.status_label.setText("Проект выбран. Нажмите «Анализировать».")
    def analyze(self)->None:
        if self.root_path is None: self.status_label.setText("Сначала выберите проект."); return
        self.status_label.setText("Индексирование и анализ проекта...")
        try:self.summary=self.controller.analyze(self.root_path)
        except (FileNotFoundError,OSError,ValueError) as error:self.status_label.setText(f"Ошибка анализа: {error}"); return
        self._show_summary(self.summary)
    def _show_summary(self,summary:ArchitectureSummary)->None:
        self.project_label.setText(f"{summary.project_name} — {summary.project_path}")
        for key,label in self.metrics.items():label.setText(str(getattr(summary,key)))
        self.dependencies.clear(); self.modules.clear(); self.module_details.clear(); self.warnings.clear(); self.dependencies.addItems(summary.dependencies or ("Внутренние зависимости пока не обнаружены",)); self.modules.addItems([f"{x.name}  [{x.risk_level}: {x.risk_score}]" for x in summary.module_details]); self.warnings.addItems(summary.warnings or ("Критических архитектурных предупреждений не обнаружено",)); self.graph_view.show_summary(summary)
        if summary.module_details:self.modules.setCurrentRow(0)
        cycles=f", циклов: {len(summary.cycles)}" if summary.cycles else ""; self.status_label.setText(f"Анализ завершён: {summary.nodes_total} узлов, {summary.edges_total} связей{cycles}.")
    def _select_module_by_name(self,name:str)->None:
        if self.summary is None:return
        for row,item in enumerate(self.summary.module_details):
            if item.name==name:self.modules.setCurrentRow(row); break
    def _show_module(self,row:int)->None:
        if self.summary is None or row<0 or row>=len(self.summary.module_details):self.module_details.clear(); return
        item=self.summary.module_details[row]; self.graph_view.select_module(item.name)
        depends="\n".join(f"  → {x}" for x in item.dependencies) or "  —"; used="\n".join(f"  ← {x}" for x in item.dependents) or "  —"; symbols="\n".join(f"  {x}" for x in item.symbols) or "  —"
        self.module_details.setPlainText(f"Модуль: {item.name}\nФайл: {item.path}\n\nРиск: {item.risk_level} ({item.risk_score}/100)\nСвязанность: {item.coupling}\nИсходящих зависимостей: {len(item.dependencies)}\nВходящих зависимостей: {len(item.dependents)}\n\nЗависит от:\n{depends}\n\nИспользуется в:\n{used}\n\nСимволы:\n{symbols}")
