import sys
import random
import time
import html
import math
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

TRACK_START = 100
TRACK_END = 1750
CENTER = 900

VISUALIZATION_SECTIONS = [
    {
        "title": "Importe",
        "description": "Lädt Standardbibliothek und PyQt6 für Logik, Zeitsteuerung und Oberfläche.",
        "color": "#4FC3F7",
        "background": "#0D2533",
        "marker": "import sys",
    },
    {
        "title": "Globale Konstanten",
        "description": "Definiert die festen Streckenpositionen für Start, Ende und Bahnsteigmitte.",
        "color": "#80CBC4",
        "background": "#12312D",
        "marker": "TRACK_START = 100",
    },
    {
        "title": "Code-Visualisierung",
        "description": "Öffnet das zweite Fenster und markiert, welcher Codeteil für welchen Programmteil zuständig ist.",
        "color": "#BA68C8",
        "background": "#26152F",
        "marker": "class CodeVisualizationWindow(QMainWindow):",
    },
    {
        "title": "3D-Bahnhof",
        "description": "Erzeugt die dreh- und zoombare 3D-Ansicht des Bahnhofs mit Bahnsteigen und Zügen im dritten Fenster.",
        "color": "#4DD0E1",
        "background": "#0E2B30",
        "marker": "class Station3DWidget(QWidget):",
    },
    {
        "title": "Datenklassen",
        "description": "Beschreibt die Datenstrukturen für Gleise und Züge.",
        "color": "#64B5F6",
        "background": "#10273B",
        "marker": "class Track:",
    },
    {
        "title": "Stellwerkslogik",
        "description": "Vergibt Gleise, meldet Belegung und gibt Fahrwege wieder frei.",
        "color": "#81C784",
        "background": "#172A1A",
        "marker": "class Interlocking:",
    },
    {
        "title": "Haupt-GUI",
        "description": "Erzeugt die Oberfläche, Tabellen, Signale, Logs sowie die Buttons und Fenster für Visualisierung und 3D-Ansicht.",
        "color": "#FFB74D",
        "background": "#33240F",
        "marker": "class StellwerkGUI(QMainWindow):",
    },
    {
        "title": "Simulation",
        "description": "Steuert Zugerzeugung, Bewegung, Halt und Abfahrt.",
        "color": "#E57373",
        "background": "#331717",
        "marker": "class Simulation:",
    },
    {
        "title": "Programmstart",
        "description": "Initialisiert QApplication, GUI und Simulation und startet die Anwendung.",
        "color": "#B0BEC5",
        "background": "#1E262A",
        "marker": "def main():",
    },
]


class CodeVisualizationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Code-Visualisierung")
        self.resize(1400, 900)

        self.legend = QTextBrowser()
        self.legend.setReadOnly(True)
        self.legend.setMaximumHeight(260)
        self.legend.setStyleSheet("""
            QTextBrowser {
                background-color: #111111;
                color: white;
                border: 1px solid #444444;
                font-size: 13px;
            }
            a {
                color: #4FC3F7;
            }
        """)

        self.code_view = QTextBrowser()
        self.code_view.setReadOnly(True)
        self.code_view.setOpenExternalLinks(False)
        self.code_view.setStyleSheet("""
            QTextBrowser {
                background-color: #0b0b0b;
                color: white;
                border: 1px solid #444444;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.code_view.setFont(QFont("Consolas", 10))

        refresh_button = QPushButton("Visualisierung aktualisieren")
        refresh_button.clicked.connect(self.load_visualization)

        layout = QVBoxLayout()
        layout.addWidget(self.legend)
        layout.addWidget(self.code_view, 1)
        layout.addWidget(refresh_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_visualization()

    def _build_section_ranges(self, lines):
        positions = []

        for section in VISUALIZATION_SECTIONS:
            for index, line in enumerate(lines):
                if line.strip().startswith(section["marker"]):
                    positions.append((index, section))
                    break

        positions.sort(key=lambda item: item[0])

        ranges = []
        for pos, (start_index, section) in enumerate(positions):
            if pos + 1 < len(positions):
                end_index = positions[pos + 1][0] - 1
            else:
                end_index = len(lines) - 1

            ranges.append({
                "section": section,
                "start": start_index,
                "end": end_index,
            })

        return ranges

    def _find_section_for_line(self, line_index, ranges):
        for entry in ranges:
            if entry["start"] <= line_index <= entry["end"]:
                return entry["section"]
        return None

    def _build_legend_html(self, ranges, source_path):
        items = []

        for entry in ranges:
            section = entry["section"]
            start_line = entry["start"] + 1
            end_line = entry["end"] + 1
            items.append(f"""
                <tr>
                    <td style="padding:8px 10px; white-space:nowrap;">
                        <span style="display:inline-block; width:14px; height:14px; background:{section['color']};
                                     border:1px solid #666666; vertical-align:middle; margin-right:8px;"></span>
                        <b>{html.escape(section['title'])}</b>
                    </td>
                    <td style="padding:8px 10px; color:#dddddd;">{html.escape(section['description'])}</td>
                    <td style="padding:8px 10px; color:#bbbbbb; white-space:nowrap;">Zeilen {start_line}-{end_line}</td>
                </tr>
            """)

        return f"""
            <div style="font-family:Segoe UI, Arial, sans-serif; padding:8px 10px;">
                <h2 style="margin:0 0 10px 0; color:#ffffff;">Code-Visualisierung</h2>
                <p style="margin:0 0 12px 0; color:#cccccc;">
                    Dieses Fenster zeigt den kompletten Quellcode und hebt farblich hervor,
                    welcher Abschnitt für welchen Programmteil verantwortlich ist.
                </p>
                <p style="margin:0 0 14px 0; color:#aaaaaa;">
                    Quelle: {html.escape(str(source_path))}
                </p>
                <table style="width:100%; border-collapse:collapse; border:1px solid #333333;">
                    <thead>
                        <tr style="background:#1a1a1a; color:#ffffff;">
                            <th style="text-align:left; padding:8px 10px;">Bereich</th>
                            <th style="text-align:left; padding:8px 10px;">Verantwortung</th>
                            <th style="text-align:left; padding:8px 10px;">Zeilen</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(items)}
                    </tbody>
                </table>
            </div>
        """

    def _build_code_html(self, lines, ranges):
        rows = []
        current_section_title = None

        for index, line in enumerate(lines):
            section = self._find_section_for_line(index, ranges)

            if section and section["title"] != current_section_title:
                current_section_title = section["title"]
                rows.append(f"""
                    <tr>
                        <td colspan="3" style="
                            background:{section['color']};
                            color:#111111;
                            font-weight:bold;
                            padding:8px 10px;
                            border-top:2px solid #000000;
                            border-bottom:1px solid #000000;
                        ">
                            {html.escape(section['title'])} - {html.escape(section['description'])}
                        </td>
                    </tr>
                """)

            escaped_line = html.escape(line.expandtabs(4))
            if escaped_line == "":
                escaped_line = "&nbsp;"

            background = section["background"] if section else "#111111"
            color = section["color"] if section else "#dddddd"
            section_name = section["title"] if section else "Nicht zugeordnet"

            rows.append(f"""
                <tr>
                    <td style="
                        width:70px;
                        padding:2px 10px;
                        text-align:right;
                        color:#888888;
                        background:#050505;
                        border-right:1px solid #222222;
                    ">{index + 1}</td>
                    <td style="
                        width:190px;
                        padding:2px 10px;
                        color:{color};
                        background:{background};
                        border-right:1px solid #222222;
                        white-space:nowrap;
                    ">{html.escape(section_name)}</td>
                    <td style="
                        padding:2px 12px;
                        background:{background};
                        color:#f2f2f2;
                        white-space:pre;
                    ">{escaped_line}</td>
                </tr>
            """)

        return f"""
            <div style="font-family:Consolas, 'Courier New', monospace;">
                <table style="width:100%; border-collapse:collapse;">
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
        """

    def load_visualization(self):
        source_path = Path(__file__)

        try:
            source_text = source_path.read_text(encoding="utf-8")
        except OSError as error:
            self.legend.setHtml(f"""
                <div style="padding:12px; color:#ffb3b3; font-family:Segoe UI, Arial, sans-serif;">
                    <h3>Code konnte nicht geladen werden</h3>
                    <p>{html.escape(str(error))}</p>
                </div>
            """)
            self.code_view.setPlainText("")
            return

        lines = source_text.splitlines()
        ranges = self._build_section_ranges(lines)

        self.legend.setHtml(self._build_legend_html(ranges, source_path))
        self.code_view.setHtml(self._build_code_html(lines, ranges))

        scrollbar = self.code_view.verticalScrollBar()
        scrollbar.setValue(0)


class Station3DWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(900, 600)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.simulation = None
        self.last_mouse_pos = None

        self.yaw = -0.95
        self.pitch = 0.62
        self.zoom = 1900.0
        self.camera_distance = 2800.0

        ordered_tracks = [6, 5, 4, 3, 2, 1]
        spacing = 170
        offset = (len(ordered_tracks) - 1) / 2
        self.track_depths = {
            track_id: (index - offset) * spacing
            for index, track_id in enumerate(ordered_tracks)
        }

        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(33)

    def set_simulation(self, simulation):
        self.simulation = simulation
        self.update()

    def reset_view(self):
        self.yaw = -0.95
        self.pitch = 0.62
        self.zoom = 1900.0
        self.update()

    def _clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def _map_track_x(self, scene_x):
        ratio = (scene_x - TRACK_START) / (TRACK_END - TRACK_START)
        return -900 + ratio * 1800

    def _rotate_point(self, point):
        x, y, z = point

        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        x1 = x * cos_yaw - z * sin_yaw
        z1 = x * sin_yaw + z * cos_yaw

        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)
        y2 = y * cos_pitch - z1 * sin_pitch
        z2 = y * sin_pitch + z1 * cos_pitch

        return x1, y2, z2

    def _project_point(self, point):
        tx, ty, tz = self._rotate_point(point)
        depth = self.camera_distance + tz

        if depth <= 80:
            return None, None

        factor = self.zoom / depth
        sx = self.width() / 2 + tx * factor
        sy = self.height() * 0.62 - ty * factor
        return QPointF(sx, sy), depth

    def _face_depth(self, points):
        depths = []

        for point in points:
            _, _, tz = self._rotate_point(point)
            depths.append(self.camera_distance + tz)

        return sum(depths) / len(depths)

    def _add_face(self, faces, points, fill_color, line_color, pen_width=1):
        faces.append({
            "points": points,
            "fill": fill_color,
            "line": line_color,
            "width": pen_width,
        })

    def _add_box(self, faces, x1, x2, y1, y2, z1, z2, fill_color, line_color, pen_width=1):
        p000 = (x1, y1, z1)
        p001 = (x1, y1, z2)
        p010 = (x1, y2, z1)
        p011 = (x1, y2, z2)
        p100 = (x2, y1, z1)
        p101 = (x2, y1, z2)
        p110 = (x2, y2, z1)
        p111 = (x2, y2, z2)

        self._add_face(faces, [p010, p110, p111, p011], fill_color, line_color, pen_width)
        self._add_face(faces, [p000, p001, p101, p100], fill_color.darker(145), line_color, pen_width)
        self._add_face(faces, [p000, p100, p110, p010], fill_color.darker(130), line_color, pen_width)
        self._add_face(faces, [p001, p011, p111, p101], fill_color.lighter(120), line_color, pen_width)
        self._add_face(faces, [p000, p010, p011, p001], fill_color.darker(150), line_color, pen_width)
        self._add_face(faces, [p100, p101, p111, p110], fill_color.lighter(110), line_color, pen_width)

    def _add_wedge(self, faces, base_x, tip_x, y1, y2, z1, z2, fill_color, line_color):
        center_z = (z1 + z2) / 2
        tip_low = (tip_x, y1, center_z)
        tip_high = (tip_x, y2 - 3, center_z)
        back_low_left = (base_x, y1, z1)
        back_low_right = (base_x, y1, z2)
        back_high_left = (base_x, y2, z1)
        back_high_right = (base_x, y2, z2)

        self._add_face(
            faces,
            [back_high_left, back_high_right, back_low_right, back_low_left],
            fill_color,
            line_color,
        )
        self._add_face(
            faces,
            [back_low_left, back_high_left, tip_high, tip_low],
            fill_color.darker(125),
            line_color,
        )
        self._add_face(
            faces,
            [back_low_right, tip_low, tip_high, back_high_right],
            fill_color.lighter(115),
            line_color,
        )
        self._add_face(
            faces,
            [back_high_left, back_high_right, tip_high],
            fill_color.lighter(110),
            line_color,
        )
        self._add_face(
            faces,
            [back_low_left, tip_low, back_low_right],
            fill_color.darker(145),
            line_color,
        )

    def _build_ground(self, faces):
        self._add_box(
            faces,
            -1100,
            1100,
            -40,
            -4,
            -620,
            620,
            QColor(82, 92, 82),
            QColor(45, 50, 45),
        )

        self._add_box(
            faces,
            -760,
            760,
            -4,
            0,
            -540,
            540,
            QColor(120, 126, 110),
            QColor(80, 80, 70),
        )

    def _build_tracks(self, faces):
        for track_id, track_z in self.track_depths.items():
            self._add_box(
                faces,
                -930,
                930,
                -1,
                2,
                track_z - 40,
                track_z + 40,
                QColor(110, 110, 105),
                QColor(60, 60, 60),
            )

            for sleeper_x in range(-900, 901, 120):
                self._add_box(
                    faces,
                    sleeper_x - 26,
                    sleeper_x + 26,
                    0,
                    6,
                    track_z - 34,
                    track_z + 34,
                    QColor(126, 92, 60),
                    QColor(74, 54, 34),
                )

            for rail_offset in (-13, 13):
                self._add_box(
                    faces,
                    -930,
                    930,
                    6,
                    12,
                    track_z + rail_offset - 2,
                    track_z + rail_offset + 2,
                    QColor(210, 210, 215),
                    QColor(100, 100, 100),
                )

            signal_x = 980 if track_id % 2 == 1 else -980
            self._add_box(
                faces,
                signal_x - 4,
                signal_x + 4,
                0,
                65,
                track_z - 4,
                track_z + 4,
                QColor(70, 70, 78),
                QColor(30, 30, 30),
            )
            self._add_box(
                faces,
                signal_x - 10,
                signal_x + 10,
                65,
                80,
                track_z - 10,
                track_z + 10,
                QColor(45, 45, 45),
                QColor(20, 20, 20),
            )

    def _build_platforms(self, faces):
        track_positions = [self.track_depths[track_id] for track_id in [6, 5, 4, 3, 2, 1]]

        for first, second in zip(track_positions, track_positions[1:]):
            platform_z = (first + second) / 2

            self._add_box(
                faces,
                -720,
                720,
                0,
                18,
                platform_z - 34,
                platform_z + 34,
                QColor(188, 188, 192),
                QColor(102, 102, 102),
            )

            self._add_box(
                faces,
                -720,
                720,
                18,
                20,
                platform_z - 34,
                platform_z - 29,
                QColor(245, 220, 90),
                QColor(150, 130, 40),
            )

            self._add_box(
                faces,
                -720,
                720,
                18,
                20,
                platform_z + 29,
                platform_z + 34,
                QColor(245, 220, 90),
                QColor(150, 130, 40),
            )

            for support_x in range(-560, 561, 280):
                self._add_box(
                    faces,
                    support_x - 4,
                    support_x + 4,
                    20,
                    98,
                    platform_z - 5,
                    platform_z + 5,
                    QColor(90, 96, 110),
                    QColor(55, 60, 70),
                )

            self._add_box(
                faces,
                -610,
                610,
                98,
                106,
                platform_z - 24,
                platform_z + 24,
                QColor(120, 150, 175),
                QColor(70, 90, 105),
            )

    def _build_trains(self, faces):
        if not self.simulation:
            return

        for train in self.simulation.trains:
            if not train.track:
                continue

            track_z = self.track_depths.get(train.track.id, 0)
            color = QColor(220, 30, 30) if train.type == "RE" else QColor(0, 175, 75)
            line = QColor(50, 50, 50)

            cars = 4 if train.type == "RE" else 3
            size = 50 if train.type == "RE" else 40
            width = 44 if train.type == "RE" else 36
            body_top = 48 if train.type == "RE" else 42
            roof_top = body_top + 6

            for i in range(cars):
                start_x = train.x + i * (size + 5)
                end_x = start_x + size

                world_x1 = self._map_track_x(start_x)
                world_x2 = self._map_track_x(end_x)

                self._add_box(
                    faces,
                    world_x1,
                    world_x2,
                    12,
                    body_top,
                    track_z - width / 2,
                    track_z + width / 2,
                    color,
                    line,
                )

                self._add_box(
                    faces,
                    world_x1 + 3,
                    world_x2 - 3,
                    body_top,
                    roof_top,
                    track_z - (width / 2 - 4),
                    track_z + (width / 2 - 4),
                    color.lighter(125),
                    line,
                )

            if train.track.direction == "WEST_EAST":
                nose_base = self._map_track_x(train.x + cars * (size + 5))
                nose_tip = self._map_track_x(train.x + cars * (size + 5) + 35)
                self._add_wedge(
                    faces,
                    nose_base,
                    nose_tip,
                    12,
                    body_top,
                    track_z - width / 2,
                    track_z + width / 2,
                    color,
                    line,
                )
            else:
                nose_base = self._map_track_x(train.x)
                nose_tip = self._map_track_x(train.x - 35)
                self._add_wedge(
                    faces,
                    nose_base,
                    nose_tip,
                    12,
                    body_top,
                    track_z - width / 2,
                    track_z + width / 2,
                    color,
                    line,
                )

    def _scene_faces(self):
        faces = []
        self._build_ground(faces)
        self._build_tracks(faces)
        self._build_platforms(faces)
        self._build_trains(faces)
        return faces

    def _draw_faces(self, painter):
        render_items = []

        for face in self._scene_faces():
            polygon_points = []
            visible = True

            for point in face["points"]:
                projected, depth = self._project_point(point)
                if projected is None or depth is None:
                    visible = False
                    break
                polygon_points.append(projected)

            if not visible:
                continue

            render_items.append({
                "polygon": QPolygonF(polygon_points),
                "fill": face["fill"],
                "line": face["line"],
                "width": face["width"],
                "depth": self._face_depth(face["points"]),
            })

        render_items.sort(key=lambda item: item["depth"], reverse=True)

        for item in render_items:
            painter.setPen(QPen(item["line"], item["width"]))
            painter.setBrush(QBrush(item["fill"]))
            painter.drawPolygon(item["polygon"])

    def _draw_labels(self, painter):
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        for track_id, track_z in self.track_depths.items():
            label_pos, depth = self._project_point((-965, 58, track_z))
            if label_pos is not None and depth is not None:
                painter.drawText(label_pos + QPointF(-18, -4), f"Gleis {track_id}")

        if self.simulation:
            train_font = QFont(font)
            train_font.setPointSize(9)
            painter.setFont(train_font)

            for train in self.simulation.trains:
                if not train.track:
                    continue

                cars = 4 if train.type == "RE" else 3
                size = 50 if train.type == "RE" else 40
                center_scene_x = train.x + (cars * (size + 5)) / 2
                center_x = self._map_track_x(center_scene_x)
                label_pos, depth = self._project_point((center_x, 78, self.track_depths[train.track.id]))
                if label_pos is not None and depth is not None:
                    painter.setPen(QPen(QColor(255, 245, 210)))
                    painter.drawText(label_pos + QPointF(-18, -6), train.number)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        background = QLinearGradient(0, 0, 0, self.height())
        background.setColorAt(0.0, QColor(20, 28, 44))
        background.setColorAt(0.55, QColor(42, 62, 78))
        background.setColorAt(1.0, QColor(54, 60, 48))
        painter.fillRect(self.rect(), background)

        painter.fillRect(0, int(self.height() * 0.62), self.width(), self.height(), QColor(45, 56, 44, 80))

        self._draw_faces(painter)
        self._draw_labels(painter)

        painter.setPen(QPen(QColor(255, 255, 255)))
        info_font = QFont("Segoe UI", 10)
        painter.setFont(info_font)

        painter.drawText(18, 28, "3D-Bahnhofsansicht")
        painter.drawText(18, 48, "Linke Maustaste: drehen   |   Mausrad: zoomen   |   Doppelklick: Ansicht zurücksetzen")

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos is None:
            return

        current_pos = event.position()
        delta = current_pos - self.last_mouse_pos
        self.last_mouse_pos = current_pos

        self.yaw += delta.x() * 0.01
        self.pitch = self._clamp(self.pitch - delta.y() * 0.01, -1.15, 1.15)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = None

    def mouseDoubleClickEvent(self, event):
        self.reset_view()

    def wheelEvent(self, event):
        step = event.angleDelta().y() / 120
        self.zoom = self._clamp(self.zoom + step * 120, 900, 3200)
        self.update()


class Station3DWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("3D-Bahnhofsansicht")
        self.resize(1400, 900)

        self.station_view = Station3DWidget()

        info = QLabel("Drehbar mit linker Maustaste, zoombar mit Mausrad. Die Züge werden live aus der Simulation übernommen.")
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                background-color: #1f1f1f;
                color: white;
                padding: 8px;
                border: 1px solid #444444;
            }
        """)

        reset_button = QPushButton("3D-Kamera zurücksetzen")
        reset_button.clicked.connect(self.station_view.reset_view)

        layout = QVBoxLayout()
        layout.addWidget(info)
        layout.addWidget(self.station_view, 1)
        layout.addWidget(reset_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def set_simulation(self, simulation):
        self.station_view.set_simulation(simulation)


class Track:
    def __init__(self, id, train_type, direction):
        self.id = id
        self.type = train_type
        self.direction = direction
        self.occupied = False
        self.train = None


class Train:
    def __init__(self, number, train_type):
        self.number = number
        self.type = train_type

        self.track = None
        self.state = "approach"

        self.x = 0
        self.speed = 2

        self.graphics = []
        self.text_item = None

        self.stop_time = 0
        self.stop_start = None


class Interlocking:
    def __init__(self, gui):
        self.gui = gui

        self.tracks = [
            Track(1, "RE", "WEST_EAST"),
            Track(2, "RE", "EAST_WEST"),
            Track(3, "RE", "WEST_EAST"),
            Track(4, "RE", "EAST_WEST"),
            Track(5, "S", "WEST_EAST"),
            Track(6, "S", "EAST_WEST")
        ]

    def request_track(self, train):
        self.gui.log(f"{train.number} → Anfrage Gleis")

        self.gui.log_comm(
            f"<b>SCI-CC</b> via <b>RaSTA</b>: Fahrweganfrage {train.number}"
        )

        for track in self.tracks:
            if track.type == train.type and not track.occupied:
                track.occupied = True
                track.train = train
                train.track = track

                self.gui.log(f"Gleis {track.id} zugewiesen ({train.number})")

                self.gui.log_comm(f"<b>SCI-TDS</b>: Gleis {track.id} BELEGT")
                self.gui.log_comm(f"<b>MQTT</b>: track/{track.id} = occupied")

                self.gui.update_table()
                return track

        self.gui.log(f"{train.number} wartet")
        return None

    def release(self, train):
        track = train.track

        if track:
            self.gui.log(f"{train.number} verlässt Gleis {track.id}")

            track.occupied = False
            track.train = None

            self.gui.log_comm(f"<b>SCI-TDS</b>: Gleis {track.id} FREI")

            self.gui.set_signal(track.id, "off")
            self.gui.update_table()


class StellwerkGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(1920, 1080)

        self.scene = QGraphicsScene()

        # >>> FIX: feste Scene-Größe definieren <<<
        self.scene.setSceneRect(0, 0, 1800, 800)

        self.view = QGraphicsView(self.scene)
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.black))

        self.logbox = QTextEdit()
        self.logbox.setReadOnly(True)

        self.comm_view = QTextEdit()
        self.comm_view.setReadOnly(True)

        self.protocol_info = QTextBrowser()
        self.protocol_info.setOpenExternalLinks(True)
        self.protocol_info.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: white;
            }
            a {
                color: white;
                text-decoration: underline;
            }
            a:hover {
                color: #aaaaaa;
            }
        """)

        self.protocol_info.setHtml("""
        <b>Protokolle & Schnittstellen:</b><br><br>
        • <a href="https://de.wikipedia.org/wiki/Rail_Safe_Transport_Application">RaSTA</a><br>
        • <a href="https://de.wikipedia.org/wiki/European_Train_Control_System">ETCS</a><br>
        • <a href="https://de.wikipedia.org/wiki/GSM-R">GSM-R</a><br>
        • <a href="https://de.wikipedia.org/wiki/MQTT">MQTT</a><br>
        • <a href="https://de.wikipedia.org/wiki/Digitales_Stellwerk#Referenzimplementierungen_einzelner_DSTW-Schnittstellen">SCI-CC / SCI-TDS / SCI-ILS</a><br>
        """)

        self.clock = QLabel()

        self.fullscreen_btn = QPushButton("Vollbild umschalten")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)

        self.visualization_btn = QPushButton("Code-Visualisierung anzeigen")
        self.visualization_btn.clicked.connect(self.show_code_visualization)

        self.station_3d_btn = QPushButton("3D-Bahnhofsansicht anzeigen")
        self.station_3d_btn.clicked.connect(self.show_3d_view)

        self.table = QTableWidget(6, 4)
        self.table.setHorizontalHeaderLabels(
            ["Gleis", "Status", "Zug", "Resthaltedauer (Sek.)"]
        )

        header = self.table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout = QHBoxLayout()
        side = QVBoxLayout()

        side.addWidget(QLabel("Gleisbelegung"))
        side.addWidget(self.table)

        side.addWidget(QLabel("Kommunikation & Schnittstellen"))
        side.addWidget(self.comm_view)

        side.addWidget(QLabel("Weiterführende Links"))
        side.addWidget(self.protocol_info)

        side.addWidget(QLabel("Stellwerk Log"))
        side.addWidget(self.logbox)

        side.addWidget(self.clock)
        side.addWidget(self.fullscreen_btn)
        side.addWidget(self.visualization_btn)
        side.addWidget(self.station_3d_btn)

        side_widget = QWidget()
        side_widget.setLayout(side)

        layout.addWidget(self.view, 3)
        layout.addWidget(side_widget, 1)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.tracks_y = {}
        self.signals = {}

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.blink_state = False
        self.blinking_tracks = set()

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_signals)
        self.blink_timer.start(400)

        self.visualization_window = CodeVisualizationWindow()
        self.station_3d_window = Station3DWindow()

        self.update_title()
        self.show_code_visualization()
        self.show_3d_view()

    def set_simulation(self, simulation):
        self.station_3d_window.set_simulation(simulation)

    def show_code_visualization(self):
        self.visualization_window.load_visualization()
        self.visualization_window.show()
        self.visualization_window.raise_()
        self.visualization_window.activateWindow()

    def show_3d_view(self):
        self.station_3d_window.show()
        self.station_3d_window.raise_()
        self.station_3d_window.activateWindow()

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # >>> FIX: immer auf feste Scene skalieren <<<
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        self.update_title()

    def update_title(self):
        self.setWindowTitle(f"Digitale Stellwerkssimulation ({self.width()}x{self.height()})")

    def log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logbox.append(f"[{timestamp}] {text}")

    def log_comm(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.comm_view.append(f"[{timestamp}] {text}")

    def update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def update_table(self):
        for i, track in enumerate(reversed(sim.interlocking.tracks)):
            self.table.setItem(i, 0, QTableWidgetItem(str(track.id)))

            if track.occupied:
                train = track.train
                remaining = 0
                if train.stop_start:
                    remaining = max(0, int(train.stop_time - (time.time() - train.stop_start)))

                self.table.setItem(i, 1, QTableWidgetItem("Belegt"))
                self.table.setItem(i, 2, QTableWidgetItem(train.number))
                self.table.setItem(i, 3, QTableWidgetItem(str(remaining)))
            else:
                self.table.setItem(i, 1, QTableWidgetItem("Frei"))
                self.table.setItem(i, 2, QTableWidgetItem(""))
                self.table.setItem(i, 3, QTableWidgetItem(""))

    def draw_tracks(self, tracks):
        layout = {6: 100, 5: 200, 4: 350, 3: 450, 2: 600, 1: 700}

        for track in tracks:
            y = layout[track.id]
            self.tracks_y[track.id] = y

            self.scene.addLine(TRACK_START, y, TRACK_END, y, QPen(Qt.GlobalColor.white, 4))

            if track.direction == "WEST_EAST":
                signal_x = TRACK_END + 20
            else:
                signal_x = TRACK_START - 40

            signal = self.scene.addEllipse(signal_x, y - 40, 20, 20,
                                           QPen(Qt.GlobalColor.white),
                                           QBrush(Qt.GlobalColor.darkGray))

            self.signals[track.id] = signal

    def set_signal(self, track_id, state):
        signal = self.signals[track_id]

        self.log_comm(f"<b>SCI-ILS</b>: Signal {track_id} → {state}")

        if state == "blink":
            self.blinking_tracks.add(track_id)
        else:
            self.blinking_tracks.discard(track_id)

            if state == "red":
                signal.setBrush(QBrush(Qt.GlobalColor.red))
            elif state == "green":
                signal.setBrush(QBrush(Qt.GlobalColor.green))
            else:
                signal.setBrush(QBrush(Qt.GlobalColor.darkGray))

    def blink_signals(self):
        self.blink_state = not self.blink_state
        for tid in self.blinking_tracks:
            color = Qt.GlobalColor.green if self.blink_state else Qt.GlobalColor.darkGreen
            self.signals[tid].setBrush(QBrush(color))


class Simulation:
    def __init__(self, gui):
        self.gui = gui
        self.interlocking = Interlocking(gui)
        self.trains = []

        self.re_numbers = ["RE1", "RE2", "RE7"]
        self.s_numbers = ["S3", "S5", "S7", "S9"]

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        self.spawn_timer = QTimer()
        self.spawn_timer.timeout.connect(self.spawn_train)
        self.spawn_timer.start(5000)

    def spawn_train(self):
        number = random.choice(self.re_numbers + self.s_numbers)
        ttype = "RE" if number.startswith("RE") else "S"

        train = Train(number, ttype)
        track = self.interlocking.request_track(train)

        if track:
            train.stop_time = 60 if ttype == "RE" else 30
            self.create_graphics(train)
            self.gui.set_signal(track.id, "blink")
            self.trains.append(train)

    def create_graphics(self, train):
        y = self.gui.tracks_y[train.track.id]
        direction = train.track.direction

        color = QColor(220, 0, 0) if train.type == "RE" else QColor(0, 200, 0)

        cars = 4 if train.type == "RE" else 3
        size = 50 if train.type == "RE" else 40

        train.x = TRACK_START if direction == "WEST_EAST" else TRACK_END

        items = []

        for i in range(cars):
            rect = self.gui.scene.addRect(
                train.x + i * (size + 5),
                y - 20,
                size,
                40,
                QPen(color),
                QBrush(color)
            )
            items.append(rect)

        if direction == "WEST_EAST":
            triangle = QPolygonF([
                QPointF(train.x + cars * (size + 5), y - 20),
                QPointF(train.x + cars * (size + 5) + 35, y),
                QPointF(train.x + cars * (size + 5), y + 20)
            ])
        else:
            triangle = QPolygonF([
                QPointF(train.x - 35, y),
                QPointF(train.x, y - 20),
                QPointF(train.x, y + 20)
            ])

        tri_item = self.gui.scene.addPolygon(triangle, QPen(color), QBrush(color))
        items.append(tri_item)

        text = self.gui.scene.addText(train.number)
        text.setDefaultTextColor(Qt.GlobalColor.black)
        text.setPos(train.x + 10, y - 15)

        train.text_item = text
        train.graphics = items

    def move_train(self, train):
        dx = train.speed if train.track.direction == "WEST_EAST" else -train.speed
        train.x += dx

        for item in train.graphics:
            item.moveBy(dx, 0)

        if train.text_item:
            train.text_item.moveBy(dx, 0)

    def remove_train(self, train):
        for g in train.graphics:
            self.gui.scene.removeItem(g)

        if train.text_item:
            self.gui.scene.removeItem(train.text_item)

        self.interlocking.release(train)
        self.trains.remove(train)

    def update(self):
        for train in list(self.trains):

            if train.state == "approach":
                self.move_train(train)

                if abs(train.x - CENTER) < 5:
                    train.state = "stop"
                    train.stop_start = time.time()

                    self.gui.log(f"{train.number} hält an Gleis {train.track.id}")
                    self.gui.log_comm(f"<b>ETCS</b>: Haltmeldung an <b>RBC</b>")
                    self.gui.set_signal(train.track.id, "red")

            elif train.state == "stop":
                if time.time() - train.stop_start > train.stop_time:
                    train.state = "depart"
                    self.gui.log(f"{train.number} fährt ab")
                    self.gui.log_comm(f"<b>RBC</b> → OBU: Fahrterlaubnis")
                    self.gui.set_signal(train.track.id, "green")

            elif train.state == "depart":
                self.move_train(train)

                if train.track.direction == "WEST_EAST":
                    if train.x > TRACK_END:
                        self.remove_train(train)
                else:
                    if train.x < TRACK_START:
                        self.remove_train(train)


def main():
    global sim

    app = QApplication(sys.argv)

    gui = StellwerkGUI()
    gui.show()

    sim = Simulation(gui)
    gui.set_simulation(sim)

    gui.draw_tracks(sim.interlocking.tracks)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
