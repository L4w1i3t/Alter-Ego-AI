import sys
from PyQt5.QtWidgets import QApplication
from gui import AlterEgo

def main():
    app = QApplication(sys.argv)
    window = AlterEgo()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()