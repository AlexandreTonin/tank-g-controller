"""
Ponto de entrada do pacote tankg (`python -m tankg`).
Inicia a GUI por padrão, ou a CLI se argumentos forem passados.
"""

import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() != "gui":
        from .cli.cli_app import run_cli
        run_cli(sys.argv[1:])
    else:
        from PySide6.QtWidgets import QApplication
        from .viewmodel.control_viewmodel import ControlViewModel
        from .view.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("Tank-G Controller")
        vm = ControlViewModel()
        window = MainWindow(vm)
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
