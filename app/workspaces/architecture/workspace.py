from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog,QGridLayout,QHBoxLayout,QLabel,QListWidget,QPushButton,QSplitter,QTextEdit,QVBoxLayout,QWidget
from app.workspaces.architecture.controller import ArchitectureSummary,ArchitectureWorkspaceController
from app.workspaces.architecture.graph_view import ArchitectureGraphView
from app.workspaces.architecture.history import ArchitectureHistoryStore

class ArchitectureWorkspace(QWidget):
    def __init__(self)->None:
        super().__init__(); self.controller=ArchitectureWorkspaceController(); self.history_store=ArchitectureHistoryStore(); self.root_path:Path|None=None; self.summary:ArchitectureSummary|None=None
        self.project_label=QLabel("Проект не выбран"); self.status_label=QLabel("Выберите локальный проект и запустите анализ."); self.health_label=QLabel("Здоровье архитектуры: —"); self.trend_label=QLabel("Динамика: —"); self.history_list=QListWidget(); self.dependencies=QListWidget(); self.warnings=QListWidget(); self.top_risks=QListWidget(); self.modules=QListWidget(); self.module_details=QTextEdit(); self.module_details.setReadOnly(True); self.graph_view=ArchitectureGraphView(); self.metrics={}; self._build_ui()
    def _build_ui(self)->None:
        layout=QVBoxLayout(self); header=QHBoxLayout(); title=QLabel("Центр архитектуры"); choose=QPushButton("Выбрать проект"); choose.clicked.connect(self.choose_project); analyze=QPushButton("Анализировать"); analyze.clicked.connect(self.analyze); header.addWidget(title); header.addStretch(); header.addWidget(choose); header.addWidget(analyze); layout.addLayout(header); layout.addWidget(self.project_label); layout.addWidget(self.status_label); layout.addWidget(self.health_label); layout.addWidget(self.trend_label)
        grid=QGridLayout(); names=[("files","Файлы"),("folders","Папки"),("modules","Модули"),("classes","Классы"),("methods","Методы"),("functions","Функции"),("imports","Импорты"),("internal_dependencies","Внутренние зависимости"),("nodes_total","Узлы графа"),("edges_total","Связи графа")]
        for i,(key,text) in enumerate(names): value=QLabel("—"); self.metrics[key]=value; row,col=i//2,(i%2)*2; grid.addWidget(QLabel(text),row,col); grid.addWidget(value,row,col+1)
        layout.addLayout(grid); layout.addWidget(QLabel("Карта модулей")); layout.addWidget(self.graph_view,2)
        split=QSplitter(Qt.Orientation.Horizontal); left=QWidget(); ll=QVBoxLayout(left); ll.addWidget(QLabel("Модули проекта")); ll.addWidget(self.modules); right=QWidget(); rl=QVBoxLayout(right); rl.addWidget(QLabel("Карточка модуля")); rl.addWidget(self.module_details); split.addWidget(left); split.addWidget(right); layout.addWidget(split,2)
        layout.addWidget(QLabel("Top Risks — приоритет проверки")); layout.addWidget(self.top_risks,1); layout.addWidget(QLabel("История здоровья архитектуры")); layout.addWidget(self.history_list,1)
        bottom=QSplitter(Qt.Orientation.Horizontal); bottom.addWidget(self.dependencies); bottom.addWidget(self.warnings); layout.addWidget(bottom,1)
        self.modules.currentRowChanged.connect(self._show_module); self.graph_view.module_selected.connect(self._select_module_by_name); self.top_risks.currentRowChanged.connect(self._select_risk_row)
    def choose_project(self)->None:
        directory=QFileDialog.getExistingDirectory(self,"Выберите папку проекта")
        if directory:self.root_path=Path(directory); self.project_label.setText(str(self.root_path)); self._show_history()
    def analyze(self)->None:
        if self.root_path is None:self.status_label.setText("Сначала выберите проект."); return
        try:self.summary=self.controller.analyze(self.root_path); self.history_store.append(self.root_path,self.summary)
        except (FileNotFoundError,OSError,ValueError) as error:self.status_label.setText(f"Ошибка анализа: {error}"); return
        self._show_summary(self.summary); self._show_history()
    def _show_history(self)->None:
        self.history_list.clear()
        if self.root_path is None:self.trend_label.setText("Динамика: —"); return
        history=self.history_store.load(self.root_path,limit=10); self.trend_label.setText(f"Динамика: {self.history_store.trend(history)}")
        if not history:self.history_list.addItem("История пока отсутствует"); return
        for item in reversed(history): self.history_list.addItem(f"{item.timestamp[:19]} | {item.health_level} {item.health_score}/100 | циклы {item.cycles} | высокий риск {item.high_risk_modules}")
    def _show_summary(self,s:ArchitectureSummary)->None:
        self.project_label.setText(f"{s.project_name} — {s.project_path}"); self.health_label.setText(f"Здоровье архитектуры: {s.health_level} ({s.health_score}/100)")
        for key,label in self.metrics.items():label.setText(str(getattr(s,key)))
        self.dependencies.clear(); self.warnings.clear(); self.top_risks.clear(); self.modules.clear(); self.module_details.clear(); self.dependencies.addItems(s.dependencies or ("Внутренние зависимости не обнаружены",)); self.warnings.addItems(s.warnings or ("Критических предупреждений нет",)); self.modules.addItems([f"{x.name} [{x.risk_level}: {x.risk_score}]" for x in s.module_details]); self.top_risks.addItems([f"#{i+1} {x.name} — {x.risk_score}/100" for i,x in enumerate(s.top_risks)] or ["Риски не обнаружены"]); self.graph_view.show_summary(s)
        if s.module_details:self.modules.setCurrentRow(0)
        self.status_label.setText(f"Анализ завершён: {s.nodes_total} узлов, {s.edges_total} связей, циклов: {len(s.cycles)}.")
    def _select_module_by_name(self,name:str)->None:
        if self.summary:
            for row,item in enumerate(self.summary.module_details):
                if item.name==name:self.modules.setCurrentRow(row); break
    def _select_risk_row(self,row:int)->None:
        if self.summary and 0<=row<len(self.summary.top_risks):self._select_module_by_name(self.summary.top_risks[row].name)
    def _show_module(self,row:int)->None:
        if not self.summary or row<0 or row>=len(self.summary.module_details):return
        item=self.summary.module_details[row]; self.graph_view.select_module(item.name)
        depends="\n".join(f"  → {x}" for x in item.dependencies) or "  —"; used="\n".join(f"  ← {x}" for x in item.dependents) or "  —"; symbols="\n".join(f"  {x}" for x in item.symbols) or "  —"; reasons="\n".join(f"  • {x}" for x in item.risk_reasons); recs="\n".join(f"  • {x}" for x in item.recommendations)
        self.module_details.setPlainText(f"Модуль: {item.name}\nФайл: {item.path}\n\nРиск: {item.risk_level} ({item.risk_score}/100)\nСвязанность: {item.coupling}\n\nПричины риска:\n{reasons}\n\nРекомендации:\n{recs}\n\nЗависит от:\n{depends}\n\nИспользуется в:\n{used}\n\nСимволы:\n{symbols}")
