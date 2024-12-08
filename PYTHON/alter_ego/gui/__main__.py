# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui.gui import AlterEgo


def check_virtual_environment():
    # If `sys.prefix` is the same as `sys.base_prefix`, then we are not in a virtual environment
    if sys.prefix == sys.base_prefix:
        print(
            "WARNING: It appears you are not running in a virtual environment.\n"
            "Running without a virtual environment may lead to unexpected crashes or dependency issues."
        )


def main():
    # Check for virtual environment
    check_virtual_environment()

    app = QApplication(sys.argv)
    window = AlterEgo()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()