
from functools import partial
from time import sleep
import os
import asyncio

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

from Util import (
    saveMission,
    readMissions,
    missionToPlot,
    checkAltitude,
    checkSpeed,
    formatInput,
    formatDimensions,
    terminalString
)

from drone_functions import (
    run_indoor,
    run_outdoor,
    get_battery,
    connect,
    get_telemetry,
    print_telemetry,
)

telemetry = [1.0, False, []]


# Create a Controller class to connect the GUI and the model
class PlannerControl:
    """Planner's Controller."""

    def __init__(self, view):
        """Controller initializer."""
        self.outdoor_mission = []
        self.indoor_mission = []
        self.relative_start_x = 0
        self.relative_start_y = 0
        self.missions = {}
        self._view = view
        self.connected = False
        self.telemetry_thread = None
        self.mission_thread = None
        # self.drone = None
        # Connect signals and slots
        self._connectSignals()
        self._loadMissions()

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
        self._view.setStatusText("Connecting...")
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = TelemetryWorker(self._view.outdoor)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self._view.setBatteryText)
        self.worker.location.connect(self._view.map.setStart)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self._view.connectButton.setEnabled(False)
        self.thread.finished.connect(
            lambda: self._view.connectButton.setEnabled(True)
        )

    def _addWaypoint(self):
        """Add waypoint via dialog."""
        ip = self._view.waypointDialog()
        if ip[1]:
            wp, wp_str, wp_text = formatInput(ip[0], self._view.outdoor)
            if not wp:
                self._view.errorDialog("Poorly formatted input. Please try again.", None)
            else:
                self.mission_str += wp_str
                self.mission.append(wp)
                self._view.addDisplayText(wp_text)

    def _updateWaypointButton(self):
        """Show/hide waypoint button."""
        if self._view.outdoor:
            if self._view.outdoorTabs.currentIndex() == 0:
                self._view.hideWaypointButton()
            else:
                self._view.showWaypointButton()

        else:
            if self._view.indoorTabs.currentIndex() == 0:
                self._view.hideWaypointButton()
            else:
                self._view.showWaypointButton()

    def _newWaypoint(self, latitude, longitude):

        altitude = self._view.altitudeInput.text()
        altitude_fl = checkAltitude(altitude)

        if altitude_fl == -1:
            self._view.errorDialog("Poorly formatted altitude input. Make sure altitude is set to be a number.", None)
            return
        if not altitude_fl:
            self._view.errorDialog("Altitude value not valid. Make sure altitude is set between 1 & 20 metres.", None)
            return

        self.outdoor_mission.append([float(latitude), float(longitude), float(altitude_fl)])
        self._view.map.addMarker(latitude, longitude, altitude_fl)
        wp_text = terminalString([float(latitude), float(longitude), float(altitude_fl)], self._view.outdoor)
        self._view.addDisplayText(wp_text)

    def _newIndoorWaypoint(self, x, y):

        altitude = self._view.altitudeInputGrid.text()
        altitude_fl = checkAltitude(altitude)

        if altitude_fl == -1:
            self._view.errorDialog("Poorly formatted altitude input. Make sure altitude is set to be a number.", None)
            return
        if not altitude_fl:
            self._view.errorDialog("Altitude value not valid. Make sure altitude is set between 1 & 20 metres.", None)
            return

        if altitude_fl > 0:
            altitude_fl = -altitude_fl
        if not self.indoor_mission:
            self.relative_start_x = x
            self.relative_start_y = y
            relative_x = 0
            relative_y = 0
        else:
            relative_x = x - self.relative_start_x
            relative_y = y - self.relative_start_y

        self.indoor_mission.append([float(relative_x), float(relative_y), altitude_fl, 0.0])
        self._view.grid.chart.add_point(x, y)
        wp_text = terminalString([float(relative_x), float(relative_y), altitude_fl], self._view.outdoor)
        self._view.addDisplayText(wp_text)

    def _removeIndoorWaypoint(self):
        self.indoor_mission = self.indoor_mission[:-1]
        self._view.grid.chart.remove_point()

    def _clearMission(self):
        """Clear current mission."""
        if self._view.outdoor:
            self.outdoor_mission = []
            self._view.map.clearMap()
        else:
            self.indoor_mission = []
            self._view.grid.chart.clear_plot()

    def _runMission(self):
        """Run the mission using drone functions."""
        if self._view.outdoor:
            print(self.outdoor_mission)
            # Step 2: Create a QThread object
            self.mission_thread = QThread()
            # Step 3: Create a worker object
            self.worker = MissionWorker(self.outdoor_mission, self._view.outdoor)
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
            self._view.buttons["Run Mission  "].setEnabled(False)
            self.mission_thread.finished.connect(
                lambda: self._view.buttons["Run Mission  "].setEnabled(True)
            )
        else:
            print(self.indoor_mission)
            # Step 2: Create a QThread object
            self.mission_thread = QThread()
            # Step 3: Create a worker object
            self.worker = MissionWorker(self.indoor_mission, self._view.outdoor)
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
            self._view.buttons["Run Mission  "].setEnabled(False)
            self.mission_thread.finished.connect(
                lambda: self._view.buttons["Run Mission  "].setEnabled(True)
            )

    def _emptyMissionError(self, status):
        if not status:
            self._view.errorDialog("Mission is empty. Please add at least one waypoint.", None)

    def _changeMissionMode(self):
        if self._view.outdoor:
            self._view.setIndoorPlanner()
            self._view.outdoor = False
        else:
            self._view.setOutdoorPlanner()
            self._view.outdoor = True

    def _setAltitude(self):

        altitude = self._view.altitudeInput.text()
        altitude_fl = checkAltitude(altitude)

        if altitude_fl == -1:
            self._view.errorDialog("Poorly formatted altitude input. Make sure altitude is set to be a number.", None)
            return
        if not altitude_fl:
            self._view.errorDialog("Altitude value not valid. Make sure altitude is set between 1 & 20 metres.", None)
            return

        self._view.changeAltitudeFocus()
        
    def _setSpeed(self):

        speed = self._view.speedInput.text()
        speed_fl = checkSpeed(speed)

        if speed_fl == -1:
            self._view.errorDialog("Poorly formatted speed input. Make sure speed is set to be a number.", None)
            return
        if not speed_fl:
            self._view.errorDialog("Speed value not valid. Make sure speed is set between 0.1 & 5.0 metres per second.",
                                   None)
            return

        self._view.changeAltitudeFocus()

    def _updateBlueprints(self):
        uploadDialog = QFileDialog.getOpenFileName(self._view, 'Select Your Blueprint Image', os.getcwd(),
                                                   'Image files (*.jpg *.png)')
        if uploadDialog[1]:
            dimensionsInput = self._view.blueprintDialog()
            if dimensionsInput[1]:
                dimensions = formatDimensions(dimensionsInput[0])
                if dimensions:
                    path = uploadDialog[0]
                    self._view.grid.chart.change_image(path)
                    self._view.setDimensions(dimensions)
                else:
                    self._view.errorDialog("Poorly formatted dimensions input. Make sure 2 numbers are entered for "
                                           "width and height separated by a comma.", None)

    def _saveMission(self):
        name_ip = self._view.saveDialog()

        if name_ip[1]:
            mission_name = name_ip[0]
            if not mission_name:
                self._view.errorDialog("Mission name cannot be blank.", None)
                return

        saveMission(mission_name, (self.relative_start_x, self.relative_start_y),
                    self.indoor_mission, self.outdoor_mission)
        self._view.addSavedMission(mission_name)
        self.missions[mission_name] = [(self.relative_start_x, self.relative_start_y),
                                       self.indoor_mission, self.outdoor_mission]

    def _loadMission(self, index):
        if index == 0:
            return
        print(index)
        key = list(self.missions.keys())[index-1]
        saved_mission = self.missions[key]
        self.relative_start_x = saved_mission[0][0]
        self.relative_start_y = saved_mission[0][1]
        self.indoor_mission = saved_mission[1]
        print(self.indoor_mission)
        if self.indoor_mission:
            indoor_plot = missionToPlot(self.indoor_mission, (self.relative_start_x, self.relative_start_y))
            self._view.grid.chart.set_plot(indoor_plot)
        self.outdoor_mission = saved_mission[2]
        print(self.outdoor_mission)
        if self.outdoor_mission:
            self._view.map.setMap(self.outdoor_mission)

    def _loadMissions(self):
        self.missions = readMissions()
        for name in self.missions.keys():
            self._view.addSavedMission(name)

    def _connectSignals(self):
        """Connect signals and slots."""
        self._view.buttons[" Add Waypoint"].clicked.connect(partial(self._addWaypoint))
        self._view.buttons["  Clear Mission"].clicked.connect(partial(self._clearMission))
        self._view.buttons["  Save Mission"].clicked.connect(partial(self._saveMission))
        # self._view.buttons["Run Mission  "].clicked.connect(partial(self._runMission))
        self._view.connectButton.clicked.connect(partial(self._threadTest))
        self._view.dropdown.currentIndexChanged.connect(partial(self._changeMissionMode))
        self._view.savedDropdown.currentIndexChanged.connect(partial(self._loadMission))
        self._view.outdoorTabs.currentChanged.connect(partial(self._updateWaypointButton))
        self._view.indoorTabs.currentChanged.connect(partial(self._updateWaypointButton))
        self._view.map.newWaypoint.connect(partial(self._newWaypoint))
        self._view.grid.chart.newWaypoint.connect(partial(self._newIndoorWaypoint))
        self._view.grid.chart.removeWaypoint.connect(partial(self._removeIndoorWaypoint))
        self._view.altitudeInputButton.clicked.connect(partial(self._setAltitude))
        self._view.altitudeInputButtonGrid.clicked.connect(partial(self._setAltitude))
        self._view.speedInputButton.clicked.connect(partial(self._setSpeed))
        self._view.zoomIncrease.clicked.connect(partial(self._view.grid.chart.increase_size))
        self._view.zoomDecrease.clicked.connect(partial(self._view.grid.chart.decrease_size))
        self._view.snapCheck.clicked.connect(partial(self._view.grid.chart.set_snap))
        self._view.blueprintCheck.clicked.connect(partial(self._view.grid.chart.set_blank))
        self._view.missionGripperButton.clicked.connect(partial(self._view.setGripperRemove))
        self._view.missionGripperButtonRemove.clicked.connect(partial(self._view.setGripperAdd))
        self._view.missionSeedButton.clicked.connect(partial(self._view.setSeederRemove))
        self._view.missionSeedButtonRemove.clicked.connect(partial(self._view.setSeederAdd))
        self._view.blueprintUpload.clicked.connect(partial(self._updateBlueprints))


"""
Model Functions & Classes.

Provides controller with access to drone_functions through threads 
that run parallel to the main GUI thread.
"""


def connectDrone():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(connect())
    except Exception as e:
        print(e)
        return None


class TelemetryWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(float, bool)
    armed = pyqtSignal(bool)
    location = pyqtSignal(float, float)

    def __init__(self, outdoor):
        super().__init__()
        self.outdoor = outdoor

    def run(self, ):
        sent = False
        try:
            loop = asyncio.new_event_loop()
            sleep(1)
            while True:
                connected = loop.run_until_complete(get_telemetry(telemetry, self.outdoor))
                sleep(2)
                if not connected:
                    self.finished.emit()
                if telemetry[2] and self.outdoor and not sent:
                    # print(telemetry[2].longitude_deg)
                    self.location.emit(telemetry[2].latitude_deg, telemetry[2].longitude_deg)
                    sent = True
                self.progress.emit(telemetry[0], telemetry[1])
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
                connected = loop.run_until_complete(run_outdoor(self.mission, telemetry, True))
                if not connected:
                    self.finished.emit()
            else:
                connected = loop.run_until_complete(run_indoor(self.mission))
                if not connected:
                    self.finished.emit()
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
