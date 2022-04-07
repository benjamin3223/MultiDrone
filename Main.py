
import sys

from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtWidgets import QApplication
import breeze_resources
from GUI import PlannerView
from Controller import PlannerControl


def main():
    """Main function."""
    # Create an instance of `QApplication`
    planner = QApplication(sys.argv)
    file = QFile(":/dark-purple/stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    planner.setStyleSheet(stream.readAll())
    # Show the planner's GUI
    view = PlannerView()
    view.show()
    # Create instances of the model and the controller
    PlannerControl(view=view)
    # Execute planner's main loop
    sys.exit(planner.exec_())


if __name__ == "__main__":
    main()
