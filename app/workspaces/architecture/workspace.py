from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QFileDialog,QGridLayout,QHBoxLayout,QLabel,QListWidget,QPushButton,QSplitter,QTextEdit,QVBoxLayout,QWidget
from app.workspaces.architecture.baseline import ArchitectureBaselineStore
from app.workspaces.architecture.controller import ArchitectureSummary,ArchitectureWorkspaceController
from app.workspaces.architecture.graph_view import ArchitectureGraphView
from app.workspaces.architecture.history import ArchitectureHistoryStore
from app.workspaces.architecture.quality_gate import QualityGate
from app.workspaces.architecture.quality_gate_dialog import QualityGateConfigDialog

class ArchitectureWorkspace(QWidget):
    def __init__(self)->None:
        super().__init__(); self.controller=ArchitectureWorkspaceController(); self.history_store=ArchitectureHistoryStore(); self.baseline_store=ArchitectureBaselineStore(); self.quality_gate=QualityGate(); self.root_path:Path|None=None; self.summary:ArchitectureSummary|None=None
        self.project_label=QLabel("Проект не выбран"); self.status_label=QLabel("Выберите локальный проект и запустите анализ."); self.health_label=QLabel("Здоровье архитектуры: —"); self.trend_label=QLabel("Динамика: —"); self.gate_label=QLabel("Quality Gate: —"); self.gate_config_label=QLabel("Пороги Quality Gate: —"); self.history_list=QListWidget(); self.changes_list=QListWidget(); self.baseline_list=QListWidget(); self.dependencies=QListWidget(); self.warnings=QListWidget(); self.top_risks=QListWidget(); self.modules=QListWidget(); self.module_details=QTextEdit(); self.module_details.setReadOnly(True); self.graph_view=ArchitectureGraphView(); self.metrics={}; self._build_ui()
    def _build_ui(self)->None:
        layout=QVBoxLayout(self); header=QHBoxLayout(); title=QLabel("Центр архитектуры"); choose=QPushButton("Выбрать проект"); choose.clicked.connect(self.choose_project); analyze=QPushButton("Анализировать"); analyze.clicked.connect(self.analyze); baseline=QPushButton("Зафиксировать эталон"); baseline.clicked.connect(self.save_baseline); gate_settings=QPushButton("Настроить Quality Gate"); gate_settings.clicked.connect(self.edit_quality_gate); header.addWidget(title); header.addStretch(); header.addWidget(choose); header.addWidget(analyze); header.addWidget(baseline); header.addWidget(gate_settings); layout.addLayout(header); layout.addWidget(self.project_label); layout.addWidget(self.status_label); layout.addWidget(self.health_label); layout.addWidget(self.trend_label); layout.addWidget(self.gate_label); layout.addWidget(self.gate_config_label)
        grid=QGridLayout(); names=[("files","Файлы"),("folders","Папки"),("modules","Модули"),("classes","Классы"),("methods","Методы"),("functions","Функции"),("imports","Импорты"),("internal_dependencies","Внутренние зависимости"),("nodes_total","Узлы графа"),("edges_total","Связи графа")]
        for i,(key,text) in enumerate(names): value=QLabel("—"); self.metrics[key]=value; row,col=i//2,(i%2)*2; grid.addWidget(QLabel(text),row,col); grid.addWidget(value,row,col+1)
        layout.addLayout(grid); layout.addWidget(QLabel("Карта модулей")); layout.addWidget(self.graph_view,2)
        split=QSplitter(Qt.Orientation.Horizontal); left=QWidget(); ll=QVBoxLayout(left); ll.addWidget(QLabel("Модули проекта")); ll.addWidget(self.modules); right=QWidget(); rl=QVBoxLayout(right); rl.addWidget(QLabel("Карточка модуля")); rl.addWidget(self.module_details); split.addWidget(left); split.addWidget(right); layout.addWidget(split,2)
        layout.addWidget(QLabel("Top Risks — приоритет проверки")); layout.addWidget(self.top_risks,1)
        history_split=QSplitter(Qt.Orientation.Horizontal); hb=QWidget(); hl=QVBoxLayout(hb); hl.addWidget(QLabel("История здоровья архитектуры")); hl.addWidget(self.history_list); cb=QWidget(); cl=QVBoxLayout(cb); cl.addWidget(QLabel("Изменения с прошлого анализа")); cl.addWidget(self.changes_list); bb=QWidget(); bl=QVBoxLayout(bb); bl.addWidget(QLabel("Отклонения от эталона / Quality Gate")); bl.addWidget(self.baseline_list); history_split.addWidget(hb); history_split.addWidget(cb); history_split.addWidget(bb); layout.addWidget(history_split,1)
        bottom=QSplitter(Qt.Orientation.Horizontal); bottom.addWidget(self.dependencies); bottom.addWidget(self.warnings); layout.addWidget(bottom,1)
        self.modules.currentRowChanged.connect(self._show_module); self.graph_view.module_selected.connect(self._select_module_by_name); self.top_risks.currentRowChanged.connect(self._select_risk_row)
    def choose_project(self)->None:
        directory=QFileDialog.getExistingDirectory(self,"Выберите папку проекта")
        if directory:self.root_path=Path(directory); self.project_label.setText(str(self.root_path)); self._show_history(); self._show_baseline()
    def analyze(self)->None:
        if self.root_path is None:self.status_label.setText("Сначала выберите проект."); return
        try:self.summary=self.controller.analyze(self.root_path); self.history_store.append(self.root_path,self.summary)
        except (FileNotFoundError,OSError,ValueError) as error:self.status_label.setText(f"Ошибка анализа: {error}"); return
        self._show_summary(self.summary); self._show_history(); self._show_baseline()
    def save_baseline(self)->None:
        if self.root_path is None or self.summary is None:self.status_label.setText("Сначала выполните анализ проекта."); return
        self.baseline_store.save(self.root_path,self.summary); self.status_label.setText("Архитектурный эталон сохранён."); self._show_baseline()
    def edit_quality_gate(self)->None:
        if self.root_path is None:self.status_label.setText("Сначала выберите проект."); return
        current=self.quality_gate.load_config(self.root_path); dialog=QualityGateConfigDialog(current,self)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        self.quality_gate.save_config(self.root_path,dialog.config()); self.status_label.setText("Пороги Quality Gate сохранены."); self._show_baseline()
    def _show_baseline(self)->None:
        self.baseline_list.clear()
        if self.root_path is None:self.gate_label.setText("Quality Gate: —"); self.gate_config_label.setText("Пороги Quality Gate: —"); return
        config=self.quality_gate.load_config(self.root_path); self.gate_config_label.setText(f"Пороги Quality Gate: здоровье -{config.max_health_drop}; новые циклы {config.max_new_cycles}; высокий риск {config.max_new_high_risk_modules}; рост связанности {config.max_coupling_growth}")
        baseline=self.baseline_store.load(self.root_path)
        if baseline is None:self.gate_label.setText("Quality Gate: нет эталона"); self.baseline_list.addItem("Эталон архитектуры не зафиксирован"); return
        if self.summary is None:self.gate_label.setText("Quality Gate: ожидает анализа"); self.baseline_list.addItem(f"Эталон от {baseline.timestamp[:19]} | здоровье {baseline.health_score}/100"); return
        changes=self.baseline_store.compare(baseline,self.summary); result=self.quality_gate.evaluate(baseline,self.summary,config)
        self.gate_label.setText(f"Quality Gate: {'PASS' if result.passed else 'FAIL'}"); self.baseline_list.addItems(changes)
        if result.violations:self.baseline_list.addItem("— Нарушения Quality Gate —"); self.baseline_list.addItems(result.violations)
    def _show_history(self)->None:
        self.history_list.clear(); self.changes_list.clear()
        if self.root_path is None:self.trend_label.setText("Динамика: —"); return
        history=self.history_store.load(self.root_path,limit=10); self.trend_label.setText(f"Динамика: {self.history_store.trend(history)}")
        if not history:self.history_list.addItem("История пока отсутствует"); self.changes_list.addItem("Сравнивать пока нечего"); return
        for item in reversed(history): self.history_list.addItem(f"{item.timestamp[:19]} | {item.health_level} {item.health_score}/100 | циклы {item.cycles} | высокий риск {item.high_risk_modules}")
        if len(history)<2:self.changes_list.addItem("Нужны минимум два анализа"); return
        delta=self.history_store.compare(history[-2],history[-1]); self.changes_list.addItem(f"Здоровье: {delta.health_delta:+d}")
        for value in delta.added_cycles:self.changes_list.addItem(f"Новый цикл: {value}")
        for value in delta.removed_cycles:self.changes_list.addItem(f"Устранён цикл: {value}")
        for value in delta.new_high_risk_modules:self.changes_list.addItem(f"Новый высокий риск: {value}")
        for value in delta.resolved_high_risk_modules:self.changes_list.addItem(f"Риск устранён: {value}")
        for value in delta.coupling_changes:self.changes_list.addItem(f"Связанность: {value}")
        if self.changes_list.count()==1 and delta.health_delta==0:self.changes_list.addItem("Структурных изменений не обнаружено")
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
