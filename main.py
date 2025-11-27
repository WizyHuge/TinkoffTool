import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
app = QApplication(sys.argv)

from ui.main_window import MainWindow

if __name__ == "__main__":
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    
    sys.exit(app.exec())