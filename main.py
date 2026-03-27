import sys
import random
import time
from datetime import datetime

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

TRACK_START = 100
TRACK_END = 1750
CENTER = 900


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

        self.update_title()

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
        layout = {6:100,5:200,4:350,3:450,2:600,1:700}

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

    gui.draw_tracks(sim.interlocking.tracks)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
