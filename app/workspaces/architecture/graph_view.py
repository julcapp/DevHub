from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QPen, QPolygonF
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView

from app.workspaces.architecture.controller import ArchitectureSummary


class ArchitectureGraphView(QGraphicsView):
    """Интерактивная карта внутренних зависимостей модулей."""

    module_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setMinimumHeight(260)
        self._nodes: dict[str, QGraphicsEllipseItem] = {}
        self._edges: list[tuple[str, str, QGraphicsLineItem]] = []
        self._cycle_modules: set[str] = set()
        self._risk_levels: dict[str, str] = {}

    def show_summary(self, summary: ArchitectureSummary) -> None:
        scene = self.scene(); scene.clear(); self._nodes.clear(); self._edges.clear()
        self._cycle_modules = {name for cycle in summary.cycles for name in cycle}
        self._risk_levels = {module.name: module.risk_level for module in summary.module_details}
        modules = list(summary.module_details)
        if not modules:
            scene.addText("Модули для отображения не обнаружены"); return
        radius = max(140.0, len(modules) * 28.0); center = QPointF(radius + 120.0, radius + 100.0)
        positions: dict[str, QPointF] = {}
        for index, module in enumerate(modules):
            angle = 2.0 * math.pi * index / len(modules)
            positions[module.name] = QPointF(center.x() + radius * math.cos(angle), center.y() + radius * math.sin(angle))
        module_names = {item.name for item in modules}
        for module in modules:
            for target_name in module.dependencies:
                if target_name in module_names: self._add_arrow(module.name, target_name, positions[module.name], positions[target_name])
        for module in modules:
            position = positions[module.name]; node = QGraphicsEllipseItem(-38,-38,76,76); node.setPos(position)
            brush = Qt.GlobalColor.lightGray
            if module.risk_level == "Высокий": brush = Qt.GlobalColor.lightCoral
            elif module.risk_level == "Средний": brush = Qt.GlobalColor.lightYellow
            node.setBrush(QBrush(brush)); node.setPen(QPen(Qt.GlobalColor.darkRed if module.name in self._cycle_modules else Qt.GlobalColor.darkGray, 2.5 if module.name in self._cycle_modules else 1.5))
            node.setToolTip(f"{module.name}\nРиск: {module.risk_level} ({module.risk_score}/100)\nСвязанность: {module.coupling}")
            node.setData(0,module.name); node.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable,True); scene.addItem(node); self._nodes[module.name] = node
            label = QGraphicsSimpleTextItem(module.name); label.setPos(position.x()-label.boundingRect().width()/2,position.y()+43); scene.addItem(label)
        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-40,-40,40,40)); self.fitInView(scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)

    def select_module(self, name: str) -> None:
        node = self._nodes.get(name)
        if node is None: return
        for item in self._nodes.values(): item.setSelected(False)
        node.setSelected(True); self._highlight(name); self.centerOn(node)

    def _highlight(self, name: str) -> None:
        related = {name}
        for source,target,_ in self._edges:
            if source == name: related.add(target)
            if target == name: related.add(source)
        for module,node in self._nodes.items():
            cycle = module in self._cycle_modules
            width = 3.0 if module == name else (2.5 if cycle else 1.5)
            color = Qt.GlobalColor.darkRed if cycle else (Qt.GlobalColor.black if module in related else Qt.GlobalColor.gray)
            node.setPen(QPen(color,width))
        for source,target,line in self._edges:
            active = source == name or target == name
            line.setPen(QPen(Qt.GlobalColor.black if active else Qt.GlobalColor.lightGray,2.4 if active else 1.0))

    def _add_arrow(self, source_name: str, target_name: str, source: QPointF, target: QPointF) -> None:
        scene = self.scene(); line = QGraphicsLineItem(source.x(),source.y(),target.x(),target.y()); line.setPen(QPen(Qt.GlobalColor.darkGray,1.2)); scene.addItem(line); self._edges.append((source_name,target_name,line))
        angle = math.atan2(target.y()-source.y(),target.x()-source.x()); size=10.0
        left=QPointF(target.x()-size*math.cos(angle-0.45),target.y()-size*math.sin(angle-0.45)); right=QPointF(target.x()-size*math.cos(angle+0.45),target.y()-size*math.sin(angle+0.45))
        arrow=scene.addPolygon(QPolygonF([target,left,right]),QPen(Qt.GlobalColor.darkGray),QBrush(Qt.GlobalColor.darkGray)); arrow.setZValue(1)

    def wheelEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor,factor)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().mouseReleaseEvent(event)
        for item in self.scene().selectedItems():
            module_name=item.data(0)
            if module_name:
                name=str(module_name); self._highlight(name); self.module_selected.emit(name); break
