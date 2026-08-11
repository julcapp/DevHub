from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QPen, QPolygonF
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView

from app.workspaces.architecture.controller import ArchitectureSummary


class ArchitectureGraphView(QGraphicsView):
    """Простая интерактивная карта внутренних зависимостей модулей."""

    module_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setMinimumHeight(260)

    def show_summary(self, summary: ArchitectureSummary) -> None:
        scene = self.scene()
        scene.clear()
        modules = list(summary.module_details)
        if not modules:
            scene.addText("Модули для отображения не обнаружены")
            return

        radius = max(140.0, len(modules) * 28.0)
        center = QPointF(radius + 120.0, radius + 100.0)
        positions: dict[str, QPointF] = {}
        for index, module in enumerate(modules):
            angle = 2.0 * math.pi * index / len(modules)
            positions[module.name] = QPointF(
                center.x() + radius * math.cos(angle),
                center.y() + radius * math.sin(angle),
            )

        module_names = {item.name for item in modules}
        for module in modules:
            source = positions[module.name]
            for target_name in module.dependencies:
                if target_name not in module_names:
                    continue
                self._add_arrow(source, positions[target_name])

        for module in modules:
            position = positions[module.name]
            node = QGraphicsEllipseItem(-38, -38, 76, 76)
            node.setPos(position)
            node.setBrush(QBrush(Qt.GlobalColor.lightGray))
            node.setPen(QPen(Qt.GlobalColor.darkGray, 1.5))
            node.setData(0, module.name)
            node.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
            scene.addItem(node)
            label = QGraphicsSimpleTextItem(module.name)
            label.setPos(position.x() - label.boundingRect().width() / 2, position.y() + 43)
            scene.addItem(label)

        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _add_arrow(self, source: QPointF, target: QPointF) -> None:
        scene = self.scene()
        line = QGraphicsLineItem(source.x(), source.y(), target.x(), target.y())
        line.setPen(QPen(Qt.GlobalColor.darkGray, 1.2))
        scene.addItem(line)
        angle = math.atan2(target.y() - source.y(), target.x() - source.x())
        tip = target
        size = 10.0
        left = QPointF(tip.x() - size * math.cos(angle - 0.45), tip.y() - size * math.sin(angle - 0.45))
        right = QPointF(tip.x() - size * math.cos(angle + 0.45), tip.y() - size * math.sin(angle + 0.45))
        arrow = scene.addPolygon(QPolygonF([tip, left, right]), QPen(Qt.GlobalColor.darkGray), QBrush(Qt.GlobalColor.darkGray))
        arrow.setZValue(1)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().mouseReleaseEvent(event)
        for item in self.scene().selectedItems():
            module_name = item.data(0)
            if module_name:
                self.module_selected.emit(str(module_name))
                break
