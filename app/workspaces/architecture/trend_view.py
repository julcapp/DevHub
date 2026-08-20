from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from app.workspaces.architecture.analytics import ArchitectureRunRecord


class ArchitectureTrendView(QWidget):
    """Компактный график динамики здоровья и high-risk модулей по CI-запускам."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._records: tuple[ArchitectureRunRecord, ...] = ()
        self.setMinimumHeight(150)
        self.setToolTip("Сплошная линия — здоровье архитектуры; пунктир — количество high-risk модулей")

    @property
    def records(self) -> tuple[ArchitectureRunRecord, ...]:
        return self._records

    def set_records(self, records: tuple[ArchitectureRunRecord, ...]) -> None:
        self._records = records
        self.update()

    def _points(self, values: list[int], area: QRectF, minimum: int, maximum: int) -> QPolygonF:
        if not values:
            return QPolygonF()
        span = max(1, maximum - minimum)
        x_step = area.width() / max(1, len(values) - 1)
        points = []
        for index, value in enumerate(values):
            x = area.left() + index * x_step
            ratio = (value - minimum) / span
            y = area.bottom() - ratio * area.height()
            points.append(QPointF(x, y))
        return QPolygonF(points)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        text_color = palette.color(palette.ColorRole.Text)
        accent = palette.color(palette.ColorRole.Highlight)
        secondary = palette.color(palette.ColorRole.Mid)

        rect = QRectF(self.rect()).adjusted(42, 12, -12, -28)
        painter.setPen(QPen(secondary, 1))
        painter.drawRect(rect)
        painter.setPen(text_color)

        if not self._records:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Нет данных CI для графика")
            return

        health = [item.health_score for item in self._records]
        risks = [len(item.high_risk_modules) for item in self._records]

        for value in (0, 50, 100):
            y = rect.bottom() - (value / 100) * rect.height()
            painter.setPen(QPen(secondary, 1, Qt.PenStyle.DotLine))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(text_color)
            painter.drawText(QRectF(0, y - 9, 38, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(value))

        health_points = self._points(health, rect, 0, 100)
        painter.setPen(QPen(accent, 2))
        if len(health_points) == 1:
            painter.drawEllipse(health_points[0], 3, 3)
        else:
            painter.drawPolyline(health_points)

        max_risk = max(1, max(risks))
        risk_points = self._points(risks, rect, 0, max_risk)
        painter.setPen(QPen(text_color, 2, Qt.PenStyle.DashLine))
        if len(risk_points) == 1:
            painter.drawEllipse(risk_points[0], 3, 3)
        else:
            painter.drawPolyline(risk_points)

        painter.setPen(text_color)
        first = self._records[0].run_id or "1"
        last = self._records[-1].run_id or str(len(self._records))
        painter.drawText(QRectF(rect.left(), rect.bottom() + 5, rect.width() / 2, 20), Qt.AlignmentFlag.AlignLeft, f"run {first}")
        painter.drawText(QRectF(rect.center().x(), rect.bottom() + 5, rect.width() / 2, 20), Qt.AlignmentFlag.AlignRight, f"run {last}")
        painter.drawText(QRectF(rect.right() - 120, rect.top(), 115, 20), Qt.AlignmentFlag.AlignRight, f"high-risk max: {max(risks)}")
