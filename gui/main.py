import sys
import os
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from gui import AlterEgo

# Function to handle uncaught exceptions
def log_crash_report(exc_type, exc_value, exc_traceback):
    # Ensure crash_reports folder exists
    crash_report_folder = os.path.join(os.path.dirname(__file__), 'crash_reports')
    if not os.path.exists(crash_report_folder):
        os.makedirs(crash_report_folder)
    
    # Create a unique file name based on the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    crash_report_file = os.path.join(crash_report_folder, f"crash_report_{timestamp}.txt")

    # Collect crash details
    with open(crash_report_file, 'w') as file:
        file.write(f"Crash Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write("="*60 + "\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=file)
        file.write("="*60 + "\n")
        file.write("End of crash report\n")
    
    # Print crash to console (optional)
    traceback.print_exception(exc_type, exc_value, exc_traceback)

# Function to start the application
def main():
    # Set the exception hook to log unhandled exceptions
    sys.excepthook = log_crash_report

    app = QApplication(sys.argv)
    window = AlterEgo()
    window.show()

    # Execute the application
    try:
        sys.exit(app.exec_())
    except Exception:
        # Catch any unexpected errors during execution
        log_crash_report(*sys.exc_info())

if __name__ == "__main__":
    main()
