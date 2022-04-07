
from functools import partial
from time import sleep
from threading import Thread
import asyncio

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from drone_functions import (
    run_indoor,
    run_outdoor,
    get_battery,
    connect,
    get_telemetry,
    print_telemetry)

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
        self._view.setStatusText("Connecting...")
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = BatteryWorker(self._view.outdoor)
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
        altitude = self._view.altitudeInput.text()
        self.outdoor_mission.append([float(latitude), float(longitude), float(altitude)])

    def _newIndoorWaypoint(self, x, y):
        altitude = self._view.altitudeInputGrid.text()
        altitude_fl = float(altitude)
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

    def _removeIndoorWaypoint(self):
        self.indoor_mission = self.indoor_mission[:-1]

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
        # filename = self._view.fileDialog()
        # self.mission_str = self.mission_str[:-2] + "]"
        # status = self._run(self.mission, self._view.outdoor)
        # if status == False:
        #     self._view.errorDialog("Mission is empty, please add at least one waypoint.", None)

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
            self._view.errorDialog("Mission is empty please add at least one waypoint.", None)

    def _changeMissionMode(self):
        if self._view.outdoor:
            self._view.setIndoorPlanner()
            self._view.outdoor = False
        else:
            self._view.setOutdoorPlanner()
            self._view.outdoor = True

    def _setAltitude(self):
        self._view.changeAltitudeFocus()

    def _connectSignals(self):
        """Connect signals and slots."""
        self._view.buttons["Add Waypoint"].clicked.connect(partial(self._addWaypoint))
        self._view.buttons["Clear Mission"].clicked.connect(partial(self._clearMission))
        self._view.buttons["Run Mission  "].clicked.connect(partial(self._runMission))
        self._view.connectButton.clicked.connect(partial(self._threadTest))
        self._view.armButton.clicked.connect(partial(self._threadTest))
        self._view.dropdown.currentIndexChanged.connect(partial(self._changeMissionMode))
        self._view.map.newWaypoint.connect(partial(self._newWaypoint))
        self._view.grid.chart.newWaypoint.connect(partial(self._newIndoorWaypoint))
        self._view.grid.chart.removeWaypoint.connect(partial(self._removeIndoorWaypoint))
        self._view.altitudeInputButton.clicked.connect(partial(self._setAltitude))
        self._view.altitudeInputButtonGrid.clicked.connect(partial(self._setAltitude))
        self._view.zoomIncrease.clicked.connect(partial(self._view.grid.chart.increase_size))
        self._view.zoomDecrease.clicked.connect(partial(self._view.grid.chart.decrease_size))


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
    progress = pyqtSignal(float, bool)  #, float, float)
    armed = pyqtSignal(bool)
    location = pyqtSignal(float, float)

    def __init__(self, outdoor):
        super().__init__()
        self.outdoor = outdoor

    def run(self, ):
        sent = False
        try:
            loop = asyncio.new_event_loop()
            while True:
                loop.run_until_complete(get_telemetry(telemetry))
                # sleep(1)
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
