"""Application bootstrap and runtime entry point with single-instance IPC."""

import os
import sys
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QPen, QPainterPath
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .ui.theme import DARK_STYLESHEET

SERVER_NAME = f"recomp_center_ipc_{os.getuid()}"


def create_app_icon() -> QIcon:
    """Generates a modern vector-style Recomp bolt/chip icon."""
    size = 128
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background rounded container
    bg_grad = QLinearGradient(0, 0, size, size)
    bg_grad.setColorAt(0.0, QColor("#1e1b4b"))  # Deep Indigo
    bg_grad.setColorAt(1.0, QColor("#0f172a"))  # Slate Dark
    p.setBrush(bg_grad)
    p.setPen(QPen(QColor("#38bdf8"), 2))
    p.drawRoundedRect(8, 8, 112, 112, 28, 28)

    # Glowing Circuit / Chip Accents
    p.setPen(QPen(QColor("#818cf8"), 3))
    # Top and bottom nodes
    p.drawLine(34, 8, 34, 20)
    p.drawLine(64, 8, 64, 20)
    p.drawLine(94, 8, 94, 20)
    p.drawLine(34, 108, 34, 120)
    p.drawLine(64, 108, 64, 120)
    p.drawLine(94, 108, 94, 120)

    # Golden / Cyan Lightning Bolt
    path = QPainterPath()
    path.moveTo(70, 24)
    path.lineTo(36, 68)
    path.lineTo(60, 68)
    path.lineTo(52, 104)
    path.lineTo(92, 56)
    path.lineTo(68, 56)
    path.closeSubpath()

    bolt_grad = QLinearGradient(36, 24, 92, 104)
    bolt_grad.setColorAt(0.0, QColor("#38bdf8"))  # Cyan
    bolt_grad.setColorAt(0.5, QColor("#818cf8"))  # Indigo
    bolt_grad.setColorAt(1.0, QColor("#c084fc"))  # Purple

    p.setBrush(bolt_grad)
    p.setPen(QPen(QColor("#ffffff"), 1.5))
    p.drawPath(path)
    p.end()

    return QIcon(pix)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Recomp Center")
    app.setApplicationDisplayName("Recomp Center")
    app.setDesktopFileName("recomp-center")

    # Single-instance check via QLocalSocket
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(500):
        # Already running; signal existing instance to activate
        socket.write(b"ACTIVATE\n")
        socket.waitForBytesWritten(500)
        sys.exit(0)

    # Set icon and styling
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)
    app.setStyleSheet(DARK_STYLESHEET)

    # Create server for single-instance
    server = QLocalServer()
    # Remove stale socket file if it exists
    QLocalServer.removeServer(SERVER_NAME)
    server.listen(SERVER_NAME)

    window = MainWindow()
    window.setWindowIcon(app_icon)

    def on_new_connection():
        client_socket = server.nextPendingConnection()
        if client_socket:
            client_socket.readyRead.connect(lambda: _handle_client_msg(client_socket, window))

    def _handle_client_msg(sock, win):
        data = sock.readAll().data().decode("utf-8")
        if "ACTIVATE" in data:
            win.setWindowState(win.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
            win.show()
            win.raise_()
            win.activateWindow()

    server.newConnection.connect(on_new_connection)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
