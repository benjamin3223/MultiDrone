#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 11:39:32 2022

@author: Benjamin
"""

import sys
import breeze_resources
from functools import partial
from time import sleep
from threading import Thread
from mavsdk import System
import asyncio
import nest_asyncio
import shutil
import os

import folium
import geocoder
import io
import json
from branca.element import Element
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Import QApplication and the required widgets from PyQt5.QtWidgets
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QFile, QTextStream, pyqtSlot, QSize
from PyQt5.QtWidgets import QApplication, QInputDialog, QTextEdit, QSpacerItem, QLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QErrorMessage
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont

from drone_functions import (
    run_indoor,
    run_outdoor,
    get_battery,
    connect,
    get_telemetry,
    print_telemetry)

telemetry = [-1.0, False, []]


# Create a subclass of QMainWindow to setup the calculator's GUI
class Planner(QMainWindow):
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

    def _createModuleController(self):

        self.controlsLayout = QVBoxLayout()
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
        self.altitudeLabel = QLabel()
        self.altitudeLabel.setText("Waypoint Altitude:")
        self.altitudeLabel.setMaximumWidth(120)
        # self.mapControls.addWidget(self.altitudeLabel)

        self.altitudeInputLayout = QHBoxLayout()
        self.altitudeInputLayout.addWidget(self.altitudeLabel)
        self.altitudeInput = QLineEdit()
        self.altitudeInput.setMaximumWidth(75)
        self.altitudeInput.setText("2.5")
        # self.altitudeInput.text()
        self.altitudeInput.setAlignment(Qt.AlignRight)
        self.altitudeInputLabel = QLabel()
        self.altitudeInputLabel.setText("m")
        self.altitudeInputLabel.setMaximumWidth(20)
        self.altitudeInputLayout.addWidget(self.altitudeInput)
        self.altitudeInputLayout.addWidget(self.altitudeInputLabel)
        self.mapControls.addLayout(self.altitudeInputLayout)
        self.controlsLayout.addLayout(self.mapControls)

        self.gridControls = QVBoxLayout()
        self.altitudeLabelGrid = QLabel()
        self.altitudeLabelGrid.setText("Waypoint Altitude: ")
        # self.gridControls.addWidget(self.altitudeLabelGrid)

        self.altitudeInputLayoutGrid = QHBoxLayout()
        self.altitudeInputLayoutGrid.addWidget(self.altitudeLabelGrid)
        self.altitudeLabelGrid.setMaximumWidth(120)
        self.altitudeInputGrid = QLineEdit()
        self.altitudeInputGrid.setMaximumWidth(75)
        self.altitudeInputGrid.setText("2.5")
        self.altitudeInputGrid.setAlignment(Qt.AlignRight)
        self.altitudeInputLabelGrid = QLabel()
        self.altitudeInputLabelGrid.setText("m")
        self.altitudeInputLabelGrid.setMaximumWidth(20)
        self.altitudeInputLayoutGrid.addWidget(self.altitudeInputGrid)
        self.altitudeInputLayoutGrid.addWidget(self.altitudeInputLabelGrid)
        self.gridControls.addLayout(self.altitudeInputLayoutGrid)
        self.gridControls.addSpacerItem(QSpacerItem(50, 10))

        self.snapCheck = QCheckBox()
        self.snapCheck.setText("Snap to Grid")
        self.blueprintCheck = QCheckBox()
        self.blueprintCheck.setText("Show Blueprints")
        self.gridControls.addWidget(self.snapCheck)
        self.gridControls.addWidget(self.blueprintCheck)
        self.controlsLayout.addLayout(self.gridControls)
        self.controlsLayout.addSpacerItem(QSpacerItem(50, 20))

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

        self.seederWidget = QGroupBox()
        self.seederWidget.setLayout(self.seederLayout)
        self.gripperWidget = QGroupBox()
        self.gripperWidget.setLayout(self.gripperLayout)
        self.moduleTabs = QTabWidget()
        self.moduleTabs.addTab(self.seederWidget, "Seeder Module")
        self.moduleTabs.addTab(self.gripperWidget, "Gripper Module")
        self.moduleTabs.setMaximumWidth(275)

        self.moduleLayout.addWidget(self.moduleTabs)
        self.moduleLayout.addStretch()
        self.controlsLayout.addLayout(self.moduleLayout)

    def setOutdoorPlanner(self):
        # print("setting")
        # self.missionLayout.removeWidget(self.indoorTabs)
        # self.indoorTabs.deleteLater()
        # self.missionLayout.insertWidget(0, self.outdoorTabs)
        self.tabStack.setCurrentIndex(0)

    def setIndoorPlanner(self):
        # self.missionLayout.removeWidget(self.outdoorTabs)
        # self.outdoorTabs.deleteLater()
        # self.missionLayout.insertWidget(0, self.indoorTabs)
        self.tabStack.setCurrentIndex(1)

    def setBatteryText(self, text):
        self.batteryLevel.setText(str(text))

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


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        print(msg)  # Check js errors
        if 'coordinates' in msg:
            self.parent.handleConsoleMessage(msg)


class FoliumDisplay(QWidget):

    newWaypoint = pyqtSignal(float, float, name="newWaypoint")

    def __init__(self):
        super().__init__()
        self.resize(1000, 800)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.waypoint_count = 0
        self.waypoints = []
        self.layers = []
        start_coordinate = (55.8637710, -4.2635536)
        self.waypoints.append(start_coordinate)
        # outdoor_mission.append(start_coordinate)

        self.m = folium.Map(
            tiles='OpenStreetMap',  # 'Stamen Terrain',
            max_zoom=18,
            zoom_start=19,
            location=start_coordinate)

        folium.CircleMarker(
            location=start_coordinate,
            radius=10,
            popup="Start Location",
            tooltip="Start Location",
            color="#3186cc",
            fill=True,
            fill_color="#3186cc"
        ).add_to(self.m)

        # Add Custom JS to folium map
        self.m = self.addCustomJS(self.m)
        # save map data to data object
        data = io.BytesIO()
        self.m.save(data, close_file=False)

        self.webView = QWebEngineView()  # start web engine
        page = WebEnginePage(self)
        self.webView.setPage(page)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        self.layout.addWidget(self.webView)

    def refreshMap(self):
        data = io.BytesIO()
        self.m.save(data, close_file=False)

        self.webView = QWebEngineView()  # start web engine
        page = WebEnginePage(self)
        self.webView.setPage(page)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        self.layout.insertWidget(0, self.webView)

    @staticmethod
    def addCustomJS(map_object):
        my_js = f"""{map_object.get_name()}.on("click",
                 function (e) {{
                    var data = `{{"coordinates": ${{JSON.stringify(e.latlng)}}, "click": "one"}}`;
                    console.log(data)}});"""

        e = Element(my_js)
        html = map_object.get_root()
        html.script.get_root().render()
        # Insert new element or custom JS
        html.script._children[e.get_name()] = e

        return map_object

    def handleConsoleMessage(self, msg):
        data = json.loads(msg)

        if data['click'] == "one":
            lat = data['coordinates']['lat']
            lng = data['coordinates']['lng']
            # alt = self.altitude.toPlainText()
            # alt
            coords = f"latitude: {lat} longitude: {lng}"
            self.waypoint_count += 1
            # self.label.setText(coords)

            self.waypoints.append((lat, lng))
            self.newWaypoint.emit(float(lat), float(lng))

            layer = folium.TileLayer(

            )

            folium.Marker(
                [lat, lng],
                popup=f"<i>Waypoint {self.waypoint_count}   </i>",
                tooltip=f"Waypoint {self.waypoint_count}"
            ).add_to(self.m)

            folium.PolyLine(
                self.waypoints
            ).add_to(self.m)

        self.layout.removeWidget(self.webView)
        self.refreshMap()


class Grid(FigureCanvas):

    def __init__(self, parent):

        img = plt.imread("warehouse2.png")

        x = 28
        y = 16

        f = plt.figure(figsize=((2.75*x/y), 2.75), constrained_layout=True)
        f.patch.set_alpha(0.0)
        self.ax = f.add_subplot()
        self.ax.patch.set_alpha(0.0)
        self.ax.imshow(img, extent=[0, x, y, 0], alpha=0.95)
        # self.ax.set_position([0.2, 0.2, 0.6, 0.6])

        super().__init__(f)
        self.setParent(parent)

        # initialize your grid
        self.ax.set_xlim(0, x)
        self.ax.set_ylim(0, y)
        self.ax.xaxis.tick_top()
        self.ax.xaxis.set_label_position('top')
        self.ax.xaxis.set_major_locator(plt.FixedLocator(range(x)))
        self.ax.yaxis.set_major_locator(plt.FixedLocator(range(y)))
        plt.xticks(fontsize=2.5, color='lightgray')
        plt.yticks(fontsize=2.5, color='lightgray')
        self.ax.xaxis.set_tick_params(width=0.15, color='lightgray')
        self.ax.yaxis.set_tick_params(width=0.15, color='lightgray')
        self.ax.grid(lw=0.10)
        for i in self.ax.spines:
            self.ax.spines[i].set(lw=0.2, color='lightgray')

        plt.gca().invert_yaxis()

        # draw initial lines that will be updated later
        self.l, = self.ax.plot([], [], lw=0.7, linestyle='dashdot', marker='o', c='k', markersize=6, mew=0.9,
                               mec="#3186cc", mfc=(0.45490196, 0.58039216, 0.91764706, 0.5))
        self.p, = self.ax.plot([], [], lw=0, marker='.', c='r', alpha=0.25, )
        self.p_round, = self.ax.plot([], [], lw=0, marker='o', c='r', markersize=1)

        # Get a dict to store the values you need to change during runtime.
        self.rectdict = dict(
            points=[],
            round_to_int=True)

        # connect the callbacks to the figure
        f.canvas.mpl_connect('button_press_event', self.on_click)
        f.canvas.mpl_connect('motion_notify_event', self.on_move)

    # Define what to do when a mouse-click event is happening.
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == 1:  # (e.g. left-click)
            if self.rectdict['round_to_int']:
                self.rectdict['points'] += [[round(event.xdata), round(event.ydata)]]
            else:
                self.rectdict['points'] += [[event.xdata, event.ydata]]

            # if not indoor_mission:
            #     indoor_mission.append([0, 0, 0])
            if len(self.rectdict['points']) >= 1:
                self.rectdict['points'] = self.rectdict['points'][:-1]
                # indoor_mission = indoor_mission[:-1]
                plt.draw()

        elif event.button == 3:  # (e.g. right-click)
            pass

        elif event.button == 2:  # (e.g. middle-click)
            self.rectdict['round_to_int'] = not self.rectdict['round_to_int']
            if self.rectdict['round_to_int']:
                self.t2.set_visible(True)
            else:
                self.t2.set_visible(False)
            plt.draw()

        if len(self.rectdict['points']) > 0:
            self.l.set_visible(True)
            self.l.set_data(list(zip(*self.rectdict['points'])))

            plt.draw()
        else:
            self.l.set_visible(False)

    # Define what to do when a motion-event is detected
    def on_move(self, event):
        if event.inaxes != self.ax:
            return

        self.p.set_data(event.xdata, event.ydata)

        if self.rectdict['round_to_int']:
            self.p_round.set_data(round(event.xdata), round(event.ydata))

        plt.draw()


class GridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.chart = Grid(self)


class Dialog(QDialog):
    """Custom waypoint dialog."""

    def __init__(self, parent=None):
        """Initializer"""
        super().__init__(parent)
        self.setWindowTitle('QDialog')
        dlgLayout = QVBoxLayout()
        formLayout = QFormLayout()
        formLayout.addRow('x-axis:', QLineEdit())
        formLayout.addRow('y-axis:', QLineEdit())
        formLayout.addRow('z-axis:', QLineEdit())
        dlgLayout.addLayout(formLayout)
        btns = QDialogButtonBox()
        btns.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        dlgLayout.addWidget(btns)
        self.setLayout(dlgLayout)


"""
Model Functions & Classes.
"""


def connectDrone():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(connect())
    except Exception as e:
        print(e)
        return None


# Step 1: Create a worker class
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        """Long-running task."""
        for i in range(5):
            sleep(1)
            self.progress.emit(i + 1)
        self.finished.emit()


class BatteryWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(float)

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            while True:
                result = [-1.0]
                loop.run_until_complete(get_telemetry(telemetry))
                if telemetry[2]:
                    print(telemetry[2].longitude_deg)
                self.progress.emit(telemetry[0])
                sleep(5)

            self.finished.emit()
        except Exception as e:
            self.finished.emit()
            print(e)
            return e


class MissionWorker(QObject):

    def __init__(self, mission, outdoor):
        super().__init__()
        self.mission = mission
        self.outdoor = outdoor

    finished = pyqtSignal()
    progress = pyqtSignal(bool)

    def run(self):
        if not self.mission:
            self.progress.emit(False)
            self.finished.emit()
            return

        try:
            loop = asyncio.new_event_loop()
            print("Loop resolved.")
            if self.outdoor:
                loop.run_until_complete(run_outdoor(self.mission, telemetry))
            else:
                loop.run_until_complete(run_indoor(self.mission))
            self.finished.emit()
        except Exception as e:
            self.finished.emit()
            print(e)
            return e


def getBatteryLevel():
    try:
        loop = asyncio.new_event_loop()
        asyncio.ensure_future(get_battery())
        loop.run_forever()
        return 1.0
    except Exception as e:
        return e


# Second option for running a mission by using imported functions.
def runMission(mission, outdoor):
    if mission == []:
        return False
    # asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    print("Loop resolved.")
    if outdoor:
        loop.run_until_complete(run_outdoor(mission))
    else:
        loop.run_until_complete(run_indoor(mission))
    print("Mission Complete")
    return True


# Check and format input for adding waypoint.
def formatInput(waypoint_str, outdoor):
    try:
        wp_arr = waypoint_str.split(',')
    except:
        return [], "", ""

    n = len(wp_arr)
    if n > 3 or n == 0 or n < 3:
        return [], "", ""

    try:
        wp = [float(wp_arr[0]), float(wp_arr[1]), float(wp_arr[2])]
    except:
        return [], "", ""

    wp_str = "[float(" + wp_arr[0] + "), float(" + wp_arr[1] + "), float(" + wp_arr[2] + "), 0.0], "

    if outdoor:
        wp_text = "\nNext waypoint co-ordinates:        N:" + wp_arr[0] + "    W:" + wp_arr[1] + "    Alt:" + wp_arr[
            2] + "m \n"
    else:
        wp_text = "\nNext waypoint co-ordinates:        x = " + wp_arr[0] + "m    y = " + wp_arr[1] + "m    z = " + \
                  wp_arr[2] + "m \n"

    return wp, wp_str, wp_text


class ThreadWithReturnValue(Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


# Create a Controller class to connect the GUI and the model
class PlanCtrl:
    """Planner's Controller."""

    def __init__(self, model, view):
        """Controller initializer."""
        self._run = model
        self.outdoor_mission = []
        self.indoor_mission = []
        self._view = view
        self.connected = False
        self.telemetry_thread = None
        self.mission_thread = None
        # self.drone = None
        # Connect signals and slots
        self._connectSignals()

    def _connectDrone(self):
        if not self.connected:
            connectDrone()
            # if drone != None:
            #     self.connected = True
            #     self._view.connectButton.setEnabled(False)        

    def _armDrone(self):
        # battery_thread = ThreadWithReturnValue(target=getBatteryLevel())
        # battery_thread.start()
        # battery = battery_thread.join()
        battery = getBatteryLevel()
        battery_str = str(int(battery * 100))
        self._view.setBatteryText(battery_str + "%")

    def _threadTest(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = BatteryWorker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self._view.setBatteryText)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self._view.armButton.setEnabled(False)
        self.thread.finished.connect(
            lambda: self._view.armButton.setEnabled(True)
        )
        # self.thread.finished.connect(
        #     lambda: self._view.setBatteryText(0)
        # )

    def _addWaypoint(self):
        """Add waypoint via dialog."""
        ip = self._view.waypointDialog()
        if ip[1]:
            wp, wp_str, wp_text = formatInput(ip[0], self._view.outdoor)
            if not wp:
                self._view.errorDialog("Poorly formatted input, please try again.", None)
            else:
                self.mission_str += wp_str
                self.mission.append(wp)
                self._view.addDisplayText(wp_text)

    def _newWaypoint(self, latitude, longitude):
        print(latitude)
        print(longitude)
        print(self._view.altitudeInput.text())

    def _clearMission(self):
        """Clear current mission."""
        self._view.clearDisplay()
        self.mission_str = "["
        self.mission = []

    def _runMission(self):
        """Run the mission using drone functions."""
        # filename = self._view.fileDialog()
        # self.mission_str = self.mission_str[:-2] + "]"
        # status = self._run(self.mission, self._view.outdoor)
        # if status == False:
        #     self._view.errorDialog("Mission is empty, please add at least one waypoint.", None)

        # Step 2: Create a QThread object
        self.mission_thread = QThread()
        # Step 3: Create a worker object
        self.worker = MissionWorker(self.mission, self._view.outdoor)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.mission_thread)
        # Step 5: Connect signals and slots
        self.mission_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.mission_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.mission_thread.finished.connect(self.mission_thread.deleteLater)
        self.worker.progress.connect(self._emptyMissionError)
        # Step 6: Start the thread
        self.mission_thread.start()

        # Final resets
        self._view.buttons["Run Mission"].setEnabled(False)
        self.mission_thread.finished.connect(
            lambda: self._view.buttons["Run Mission"].setEnabled(True)
        )

    def _emptyMissionError(self, status):
        if not status:
            self._view.errorDialog("Mission is empty please add at least one waypoint.", None)

    def _changeMissionMode(self):
        if self._view.outdoor:
            self._view.setIndoorPlanner()
            self._view.outdoor = False
        else:
            print("setting outdoor")
            self._view.setOutdoorPlanner()
            self._view.outdoor = True

    def _connectSignals(self):
        """Connect signals and slots."""
        self._view.buttons["Add Waypoint"].clicked.connect(partial(self._addWaypoint))
        self._view.buttons["Clear Mission"].clicked.connect(partial(self._clearMission))
        self._view.buttons["Run Mission  "].clicked.connect(partial(self._runMission))
        self._view.connectButton.clicked.connect(partial(self._connectDrone))
        self._view.armButton.clicked.connect(partial(self._threadTest))
        self._view.dropdown.currentIndexChanged.connect(partial(self._changeMissionMode))
        self._view.map.newWaypoint.connect(partial(self._newWaypoint))


# Client code
def main():
    """Main function."""
    # Create an instance of `QApplication`
    planner = QApplication(sys.argv)
    file = QFile(":/dark-purple/stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    planner.setStyleSheet(stream.readAll())
    # Show the planner's GUI
    view = Planner()
    view.show()
    # Create instances of the model and the controller
    model = runMission
    PlanCtrl(model=model, view=view)
    # Execute planner's main loop
    sys.exit(planner.exec_())


if __name__ == "__main__":
    main()
