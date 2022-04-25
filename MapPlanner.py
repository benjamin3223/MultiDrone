
import folium
import geocoder
import io
import json
from branca.element import Element
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView

# Import QApplication and the required widgets from PyQt5.QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget


"""
Class to create the custom MapPlanner widget, allowing users to plot an outdoor GPS-based 
mission on an interactive Open-Source map.

"""
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
        self.drone_start = [55.860573940337495, -4.242192506790162]
        self.waypoints.append(self.drone_start)
        geo = geocoder.ip('me')
        self.gc_start = geo.latlng
        # self.waypoints.append(self.gc_start)          #  Can be used to get user location for general start location.

        self.m = folium.Map(
            tiles='OpenStreetMap',  # 'Stamen Terrain',
            max_zoom=18,
            zoom_start=19,
            location=self.drone_start)

        folium.CircleMarker(
            location=self.drone_start,
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

    """
    Clear currently plotted mission.
    """
    def clearMap(self):
        self.layout.removeWidget(self.webView)
        self.webView.deleteLater()
        self.waypoint_count = 0
        self.waypoints = []
        self.layers = []

        if not self.drone_start:

            self.m = folium.Map(
                tiles='OpenStreetMap',  # 'Stamen Terrain',
                max_zoom=18,
                zoom_start=12,
                location=self.gc_start)

        else:
            self.waypoints.append(self.drone_start)

            self.m = folium.Map(
                tiles='OpenStreetMap',  # 'Stamen Terrain',
                max_zoom=18,
                zoom_start=19,
                location=self.drone_start)

            folium.CircleMarker(
                location=self.drone_start,
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

    """
    Set start location of the mission when the drone location is acquired.
    """
    def setStart(self, lat, long):
        self.layout.removeWidget(self.webView)
        self.webView.deleteLater()
        self.waypoint_count = 0
        self.waypoints = []
        self.layers = []
        self.drone_start = (lat, long)
        self.waypoints.append(self.drone_start)

        self.m = folium.Map(
            tiles='OpenStreetMap',  # 'Stamen Terrain',
            max_zoom=18,
            zoom_start=19,
            location=self.drone_start)

        folium.CircleMarker(
            location=self.drone_start,
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

    """
    Set up a saved mission loaded in.
    """
    def setMap(self, markers):
        self.layout.removeWidget(self.webView)
        self.webView.deleteLater()
        self.waypoint_count = 0
        self.waypoints = []
        self.layers = []
        lat = markers[0][0]
        lon = markers[0][1]
        self.drone_start = (lat, lon)
        self.waypoints.append(self.drone_start)

        self.m = folium.Map(
            tiles='OpenStreetMap',  # 'Stamen Terrain',
            max_zoom=18,
            zoom_start=19,
            location=self.drone_start)

        folium.CircleMarker(
            location=self.drone_start,
            radius=10,
            popup="Start Location",
            tooltip="Start Location",
            color="#3186cc",
            fill=True,
            fill_color="#3186cc"
        ).add_to(self.m)

        wps = [self.drone_start]
        for i in range(1, len(markers)):
            wp = markers[i]
            lat = wp[0]
            lon = wp[1]
            wps.append((lat, lon))
            folium.Marker(
                (lat, lon),
                popup=f"<i><h6>Waypoint {i}</h6>"
                      f"N:{round(lat, 8)}<br>"
                      f"W:{round(lon, 8)}<br>\n"
                      f"Altitude: {wp[2]}m</i>",
                tooltip=f"Waypoint {i}"
            ).add_to(self.m)

        self.waypoint_count = len(markers)
        self.waypoints = wps

        folium.PolyLine(
            self.waypoints
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

    """
    Refresh the map to reflect most recent changes.
    """
    def refreshMap(self):
        data = io.BytesIO()
        self.m.save(data, close_file=False)

        self.webView = QWebEngineView()  # start web engine
        page = WebEnginePage(self)
        self.webView.setPage(page)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        self.layout.insertWidget(0, self.webView)

    """
    Add a marker for new waypoint.
    """
    def addMarker(self, lat, lng, alt):

        folium.Marker(
            [lat, lng],
            popup=f"<i><h6>Waypoint {self.waypoint_count}</h6>"
                  f"N:{round(lat, 8)}<br>"
                  f"W:{round(lng, 8)}<br>\n"
                  f"Altitude: {alt}m</i>",
            tooltip=f"Waypoint {self.waypoint_count}"
        ).add_to(self.m)

        self.waypoints.append((lat, lng))

        folium.PolyLine(
            self.waypoints
        ).add_to(self.m)

        self.layout.removeWidget(self.webView)
        self.refreshMap()

    """
    Add custom JavaScript to the Leaflet.js library to allow clicks to return 
    GPS co-ordinates.
    """
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

    """
    Handle click action from user.
    """
    def handleClick(self, msg):
        data = json.loads(msg)

        if data['click'] == "one":
            lat = data['coordinates']['lat']
            lng = data['coordinates']['lng']
            self.waypoint_count += 1

            self.newWaypoint.emit(float(lat), float(lng))


"""
Define overall QWebPage.
"""
class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, source_id):
        print(msg)  # Check js errors
        if 'coordinates' in msg:
            self.parent.handleClick(msg)
