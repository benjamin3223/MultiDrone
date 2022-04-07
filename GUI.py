
from MapPlanner import FoliumDisplay
from GridPlanner import GridWidget

# Import QApplication and the required widgets from PyQt5.QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QInputDialog, QTextEdit, QSpacerItem, QFrame
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QErrorMessage
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont

telemetry = [-1.0, False, []]


# Create a subclass of QMainWindow to setup the calculator's GUI
class PlannerView(QMainWindow):
    """Planner View (GUI)."""

    def __init__(self):
        """View initializer."""
        super().__init__()
        self.outdoor = True
        # Set some main window's properties
        self.setWindowTitle("MultiDrone Mission Planner")
        self.resize(1300, 700)
        # Set the central widget and the general layout
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)
        # Create the top bar and main content.
        self._createTopBar()
        self._createMissionControls()
        self._createModuleController()
        self._createMainContent()

    def _createTopBar(self):

        self.topBar = QHBoxLayout()

        self.connectButton = QPushButton(" Connect MultiDrone")
        self.connectButton.setMinimumWidth(200)
        self.connectButton.setStyleSheet("background-color:#44355B;")
        self.connectButton.setIcon(QIcon("connect4.png"))
        self.topBar.addWidget(self.connectButton)
        self.topBar.addSpacerItem(QSpacerItem(20, 10))

        self.armButton = QPushButton("Arm")
        self.armButton.setStyleSheet("background-color:#003459;")
        # self.armButton.setIcon(QIcon("arm2.png"))
        # self.topBar.addWidget(self.armButton)

        # self.topBar.addStretch(0)
        self.dropdownLabel = QLabel()
        self.dropdownLabel.setText("Select Mission Type: ")
        self.topBar.addWidget(self.dropdownLabel)
        self.topBar.addSpacerItem(QSpacerItem(2, 5))

        self.dropdown = QComboBox()
        self.dropdown.setStyleSheet('''*
            QComboBox QAbstractItemView
                {
                min-width: 150px;
                }
            ''')
        self.dropdown.addItem("Outdoor Mission")
        self.dropdown.addItem("Indoor Mission")
        self.topBar.addWidget(self.dropdown)
        self.topBar.addStretch(0)

        self.batteryLabel = QLabel()
        batteryIcon = QIcon("battery2.png")
        self.batteryLabel.setPixmap(batteryIcon.pixmap(batteryIcon.actualSize(QSize(40, 40))))
        self.topBar.addWidget(self.batteryLabel)

        self.batteryLevel = QLabel()
        self.batteryLevel.setText("No data")
        self.batteryLevel.setStyleSheet("color:#DFD9E8;")
        self.topBar.addWidget(self.batteryLevel)
        # self.topBar.addStretch(0)
        self.topBar.addSpacerItem(QSpacerItem(30, 10))

        self.armedLabel = QLabel()
        statusIcon = QIcon("arm3.png")
        self.armedLabel.setPixmap(statusIcon.pixmap(statusIcon.actualSize(QSize(60, 60))))
        self.topBar.addWidget(self.armedLabel)

        self.armedStatus = QLabel()
        self.armedStatus.setText("Disconnected")
        self.armedStatus.setStyleSheet("color:#DFD9E8;")
        self.topBar.addWidget(self.armedStatus)
        self.topBar.addSpacerItem(QSpacerItem(75, 5))

        self.generalLayout.addLayout(self.topBar)

    def _createMainContent(self):

        self.mainLayout = QHBoxLayout()
        self.missionLayout = QVBoxLayout()
        self.missionTitle = QLabel()
        self.missionTitle.setText("Route Planner")
        self.missionTitle.setFont(self.bold)
        self.missionTitle.setAlignment(Qt.AlignCenter)
        # self.missionLayout.addWidget(self.missionTitle)

        self.map = FoliumDisplay()
        self.grid = GridWidget()
        self.gridLayout = QVBoxLayout()
        self.gridLayout.addWidget(self.grid)
        self.gridLayout.setAlignment(Qt.AlignCenter)
        self.gridFrame = QFrame()
        self.gridFrame.setLayout(self.gridLayout)

        # Create terminal planners.
        self.outdoorTerminal = QTextEdit()
        self.outdoorTerminal.setReadOnly(True)
        self.indoorTerminal = QTextEdit()
        self.indoorTerminal.setReadOnly(True)

        self.outdoorTerminal.setText("\nConnect MultiDrone for starting coordinates or input starting co-ordinates "
                                     "manually... \n")
        # self.outdoorTerminal.append("\nTaking off at co-ordinates:        N: 54.2463546576    W: 4.233573422
        # Altitude: 0.0m\n")

        self.indoorTerminal.append("\nTaking off at co-ordinates:        x = 0.0m    y = 0.0m    z = 0.0m\n")

        self.outdoorTabs = QTabWidget()
        self.outdoorTabs.addTab(self.map, "Map Planner")
        self.outdoorTabs.addTab(self.outdoorTerminal, "Terminal Planner")
        self.indoorTabs = QTabWidget()
        self.indoorTabs.addTab(self.grid, "Grid Planner")
        self.indoorTabs.addTab(self.indoorTerminal, "Terminal Planner")
        # self.tabs.setTabPosition(QTabWidget.North)
        # self.tabs.resize(700, 500)

        self.tabStack = QStackedWidget()
        self.tabStack.addWidget(self.outdoorTabs)
        self.tabStack.addWidget(self.indoorTabs)
        self.missionLayout.addWidget(self.tabStack)

        """Create the buttons."""
        self.buttons = {}
        buttonsLayout = QHBoxLayout()
        # Button text.
        buttons = [
            "Add Waypoint", "Clear Mission", "Run Mission  "
        ]
        # Create the buttons and add them to the layout.
        for btnText in buttons:

            self.buttons[btnText] = QPushButton(btnText)

            if btnText == "Run Mission  ":
                self.buttons[btnText].setStyleSheet("background-color:#3186CC;")
                self.buttons[btnText].setIcon(QIcon("run.png"))
                self.buttons[btnText].setLayoutDirection(Qt.RightToLeft)

            buttonsLayout.addWidget(self.buttons[btnText])

        # Add buttonsLayout to the general layout.
        self.missionLayout.addLayout(buttonsLayout)
        self.mainLayout.addLayout(self.missionLayout)
        self.mainLayout.addSpacerItem(QSpacerItem(10, 100))
        self.mainLayout.addLayout(self.controlsLayout)
        self.mainLayout.addSpacerItem(QSpacerItem(20, 100))
        self.generalLayout.addLayout(self.mainLayout)

    def _createMissionControls(self):

        self.controlsLayout = QVBoxLayout()
        self.controlsLayout.addSpacerItem(QSpacerItem(50, 20))
        self.controlsTitle = QLabel()
        self.controlsTitle.setText("Mission Controls")
        self.bold = QFont()
        self.bold.setBold(True)
        self.bold.setPixelSize(18)
        self.controlsTitle.setFont(self.bold)
        self.controlsTitle.setAlignment(Qt.AlignHCenter)
        self.controlsLayout.addWidget(self.controlsTitle)
        self.controlsLayout.addSpacerItem(QSpacerItem(50, 10))

        self.mapControls = QVBoxLayout()
        self.mapControls.setAlignment(Qt.AlignRight)
        self.altitudeLabel = QLabel()
        self.altitudeLabel.setText("Set altitude for the next waypoint:")
        # self.altitudeLabel.setMaximumWidth(120)
        self.mapControls.addWidget(self.altitudeLabel)

        self.altitudeInputLayout = QHBoxLayout()
        self.altitudeInputLayout.setAlignment(Qt.AlignRight)
        # self.altitudeInputLayout.addWidget(self.altitudeLabel)
        self.altitudeInput = QLineEdit()
        self.altitudeInput.setMaximumWidth(75)
        self.altitudeInput.setText("2.5")
        self.altitudeInput.setAlignment(Qt.AlignRight)
        self.altitudeInputLabel = QLabel("m")
        self.altitudeInputButton = QPushButton("  Set  ")
        # self.altitudeInputLabel.setText("m")
        # self.altitudeInputLabel.setMaximumWidth(20)
        self.altitudeInputLayout.addWidget(self.altitudeInput)
        self.altitudeInputLayout.addWidget(self.altitudeInputLabel)
        self.altitudeInputLayout.addWidget(self.altitudeInputButton)
        self.altitudeInputLayout.addStretch()
        self.mapControls.addLayout(self.altitudeInputLayout)
        self.mapControls.addStretch()
        # self.controlsLayout.addLayout(self.mapControls)

        self.gridControls = QVBoxLayout()
        self.altitudeLabelGrid = QLabel()
        self.altitudeLabelGrid.setText("Set altitude for the next waypoint:")
        self.gridControls.addWidget(self.altitudeLabelGrid)

        self.altitudeInputLayoutGrid = QHBoxLayout()
        # self.altitudeInputLayoutGrid.addWidget(self.altitudeLabelGrid)
        # self.altitudeLabelGrid.setMaximumWidth(120)
        self.altitudeInputGrid = QLineEdit()
        self.altitudeInputGrid.setMaximumWidth(75)
        self.altitudeInputGrid.setText("2.5")
        self.altitudeInputGrid.setAlignment(Qt.AlignRight)
        self.altitudeInputLabelGrid = QLabel("m")
        self.altitudeInputButtonGrid = QPushButton("  Set  ")
        # self.altitudeInputLabelGrid.setText("m")
        # self.altitudeInputLabelGrid.setMaximumWidth(20)
        self.altitudeInputLayoutGrid.addWidget(self.altitudeInputGrid)
        self.altitudeInputLayoutGrid.addWidget(self.altitudeInputLabelGrid)
        self.altitudeInputLayoutGrid.addWidget(self.altitudeInputButtonGrid)
        self.altitudeInputLayoutGrid.addStretch()
        self.gridControls.addLayout(self.altitudeInputLayoutGrid)
        self.gridControls.addSpacerItem(QSpacerItem(50, 10))

        self.snapCheck = QCheckBox()
        self.snapCheck.setChecked(True)
        self.snapCheck.setLayoutDirection(Qt.LeftToRight)
        self.snapCheck.setText("     Snap to Grid")
        self.blueprintCheck = QCheckBox()
        self.blueprintCheck.setChecked(True)
        self.blueprintCheck.setLayoutDirection(Qt.LeftToRight)
        self.blueprintCheck.setText("     Show Blueprints")
        self.gridControls.addWidget(self.snapCheck)
        self.gridControls.addSpacerItem(QSpacerItem(50, 10))
        self.gridControls.addWidget(self.blueprintCheck)
        self.gridControls.addSpacerItem(QSpacerItem(50, 10))

        self.zoomLayout = QHBoxLayout()
        self.zoomLabel = QLabel("Zoom     ")
        self.zoomIncrease = QPushButton("Increase")
        self.zoomDecrease = QPushButton("Decrease")
        self.zoomLayout.addWidget(self.zoomLabel)
        self.zoomLayout.addWidget(self.zoomDecrease)
        self.zoomLayout.addWidget(self.zoomIncrease)
        self.gridControls.addLayout(self.zoomLayout)
        self.gridControls.addStretch()
        # self.controlsLayout.addLayout(self.gridControls)

        self.mapControlWidget = QFrame()
        self.mapControlWidget.setLayout(self.mapControls)
        self.gridControlWidget = QFrame()
        self.gridControlWidget.setLayout(self.gridControls)
        self.controlStack = QStackedWidget()
        self.controlStack.addWidget(self.mapControlWidget)
        self.controlStack.addWidget(self.gridControlWidget)
        self.controlsLayout.addWidget(self.controlStack)
        self.controlStack.setMaximumWidth(250)
        self.controlsLayout.addSpacerItem(QSpacerItem(50, 20))

    def _createModuleController(self):

        self.moduleLayout = QVBoxLayout()
        self.moduleTitle = QLabel()
        self.moduleTitle.setText("Module Controls")
        self.moduleTitle.setFont(self.bold)
        self.moduleTitle.setAlignment(Qt.AlignCenter)
        self.moduleLayout.addWidget(self.moduleTitle)
        self.moduleLayout.addSpacerItem(QSpacerItem(50, 10))

        self.seederLayout = QVBoxLayout()
        self.seederLabel = QLabel()
        seederImage = QIcon("seeder_module.png")
        self.seederLabel.setPixmap(seederImage.pixmap(seederImage.actualSize(QSize(100, 100))))
        self.seederLabel.setAlignment(Qt.AlignCenter)
        self.seederLayout.addWidget(self.seederLabel)

        self.seederStatus = QLabel()
        self.seederStatus.setText("Module Status:")
        # self.seederLayout.addWidget(self.seederStatus)

        self.seederControl = QLabel()
        self.seederControl.setText("Manual Control")
        self.subheading = QFont()
        self.subheading.setBold(True)
        self.subheading.setPixelSize(12)
        self.seederControl.setFont(self.subheading)
        self.seederLayout.addWidget(self.seederControl)
        self.manualSeedButton = QPushButton("Drop Seed Bomb")
        self.seederLayout.addWidget(self.manualSeedButton)

        self.seederMissionLabel = QLabel()
        self.seederMissionLabel.setText("Mission Actions")
        self.seederMissionLabel.setFont(self.subheading)
        self.seederLayout.addWidget(self.seederMissionLabel)
        self.missionSeedButton = QPushButton("Drop At Each Waypoint")
        self.seederLayout.addWidget(self.missionSeedButton)
        self.seederLayout.addStretch()

        self.gripperLayout = QVBoxLayout()
        self.gripperLabel = QLabel()
        gripperImage = QIcon("gripper_module.png")
        self.gripperLabel.setPixmap(gripperImage.pixmap(gripperImage.actualSize(QSize(90, 90))))
        self.gripperLabel.setAlignment(Qt.AlignCenter)
        self.gripperLayout.addWidget(self.gripperLabel)

        self.gripperStatus = QLabel()
        self.gripperStatus.setText("Module Status:")
        # self.gripperLayout.addWidget(self.gripperStatus)

        self.gripperControl = QLabel()
        self.gripperControl.setText("Manual Control")
        self.gripperControl.setFont(self.subheading)
        self.gripperLayout.addWidget(self.gripperControl)

        self.gripperButtonLayout = QHBoxLayout()
        self.openButton = QPushButton("Open")
        self.closeButton = QPushButton("Close")
        self.gripperButtonLayout.addWidget(self.openButton)
        self.gripperButtonLayout.addWidget(self.closeButton)
        self.gripperLayout.addLayout(self.gripperButtonLayout)

        self.gripperMissionLabel = QLabel()
        self.gripperMissionLabel.setText("Mission Actions")
        self.gripperMissionLabel.setFont(self.subheading)
        self.gripperLayout.addWidget(self.gripperMissionLabel)
        self.missionGripperButton = QPushButton("Release Grippers On Landing")
        self.gripperLayout.addWidget(self.missionGripperButton)
        self.gripperLayout.addStretch()

        self.seederWidget = QFrame()
        self.seederWidget.setLayout(self.seederLayout)
        self.gripperWidget = QFrame()
        self.gripperWidget.setLayout(self.gripperLayout)
        self.moduleTabs = QTabWidget()
        self.moduleTabs.addTab(self.seederWidget, "Seeder Module")
        self.moduleTabs.addTab(self.gripperWidget, "Gripper Module")
        self.moduleTabs.setMaximumWidth(275)

        self.moduleLayout.addWidget(self.moduleTabs)
        self.moduleLayout.addStretch()
        self.controlsLayout.addLayout(self.moduleLayout)

    def setOutdoorPlanner(self):
        self.tabStack.setCurrentIndex(0)
        self.controlStack.setCurrentIndex(0)

    def setIndoorPlanner(self):
        self.tabStack.setCurrentIndex(1)
        self.controlStack.setCurrentIndex(1)

    def changeAltitudeFocus(self):
        self.altitudeInput.clearFocus()
        self.altitudeLabelGrid.clearFocus()

    def setBatteryText(self, text, armed):
        self.batteryLevel.setText(str(round(text/1.0)*100) + "%")
        if armed:
            self.armedStatus.setText("Armed")
        else:
            self.armedStatus.setText("Disarmed")

    def setStatusText(self, text):
        self.armedStatus.setText(text)

    def setDisplayText(self, text):
        """Set display's text."""
        self.terminal.setText(text)
        self.terminal.setFocus()

    def addDisplayText(self, text):
        self.terminal.append(text)

    def displayText(self):
        """Get terminal's text."""
        return self.terminal.show()

    def clearDisplay(self):
        """Clear the terminal."""
        self.setDisplayText("")  # "Welcome to the MultiDrone Indoor Flight Planner!")
        if self.outdoor:
            self.terminal.append("\nTaking off at co-ordinates:        N: 54.2463546     W: 4.2335734     Alt: 0.0m\n")
        else:
            self.terminal.append("\nTaking off at co-ordinates:        x = 0    y = 0    z = 0\n")

    def waypointDialog(self):
        """Show waypoint dialog."""
        dlg = QInputDialog(self)
        if self.outdoor:
            ip = dlg.getText(self, "Add Waypoint", "Enter waypoint in the form Latitude,  Longitude,  Alt:",
                             QLineEdit.Normal, '', Qt.WindowFlags())
        else:
            ip = dlg.getText(self, "Add Waypoint", "Enter waypoint in the form x, y, z:", QLineEdit.Normal, '',
                             Qt.WindowFlags())
        return ip

    def fileDialog(self):
        """Show waypoint dialog."""
        dlg = QInputDialog(self)
        ip = dlg.getText(self, "Mission Filename", "Enter a file name:", QLineEdit.Normal, '', Qt.WindowFlags())
        return ip

    def errorDialog(self, msg, parent):
        """Display Error Message"""
        if parent is None:
            parent = self

        error_dlg = QErrorMessage(parent)
        error_dlg.showMessage(msg)
