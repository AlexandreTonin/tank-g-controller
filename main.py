"""
Ponto de entrada principal para a interface gráfica PySide6 (Qt Widgets).
Execute:
    python main.py
"""

import sys
from PySide6.QtWidgets import QApplication

from tankg.viewmodel.control_viewmodel import ControlViewModel
from tankg.view.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Tank-G Controller")
    app.setOrganizationName("M-Vave Community")

    viewmodel = ControlViewModel()
    window = MainWindow(viewmodel)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
