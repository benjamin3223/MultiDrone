
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Import QApplication and the required widgets from PyQt5.QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

"""
Class to create the custom GridPlanner widget, allowing users to plot an indoor relative position 
type mission with an updatable background image and scale for in context mission planning.

"""
class Grid(FigureCanvas):

    newWaypoint = pyqtSignal(float, float, name="newWaypoint")
    removeWaypoint = pyqtSignal(name="removeWaypoint")

    def __init__(self, parent):

        self.current_path = "images/warehouse2.png"
        img = plt.imread(self.current_path)

        self.x = 36
        self.y = 21
        self.h = 2.75
        self.w = self.h*self.x / self.y

        self.f = plt.figure(constrained_layout=True)  # figsize=(self.w, self.h),
        self.f.set_size_inches(self.w, self.h)
        self.f.patch.set_alpha(0.0)
        self.ax = self.f.add_subplot()
        self.ax.patch.set_alpha(0.0)
        # self.ax.set_position([0.2, 0.2, 0.6, 0.6])

        super().__init__(self.f)
        self.setParent(parent)

        # initialize your grid
        self.ax.set_xlim(0, self.x)
        self.ax.set_ylim(0, self.y)
        self.ax.xaxis.tick_top()
        self.ax.xaxis.set_label_position('top')
        self.ax.xaxis.set_major_locator(plt.FixedLocator(range(self.x)))
        self.ax.yaxis.set_major_locator(plt.FixedLocator(range(self.y)))
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

        self.ax.imshow(img, extent=[0, self.x, self.y, 0], alpha=0.95)

        # connect the callbacks to the figure
        self.f.canvas.mpl_connect('button_press_event', self.on_click)
        # self.f.canvas.mpl_connect('motion_notify_event', self.on_move)

    """
    On click listener function for grid. Emits signals to Controller for handling of mission/waypoints.
    """
    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        # Add a waypoint.
        if event.button == 1:  # (left-click)
            if self.rectdict['round_to_int']:
                self.newWaypoint.emit(float(round(event.xdata)), float(round(event.ydata)))
            else:
                self.newWaypoint.emit(float(event.xdata), float(event.ydata))

        # Remove last waypoint.
        elif event.button == 3:  # (right-click)
            if len(self.rectdict['points']) >= 1:
                self.removeWaypoint.emit()
                plt.draw()

        # Snap to grid options.
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

    """
    On move listener. Not currently used due to poor responsiveness.
    """
    def on_move(self, event):
        if event.inaxes != self.ax:
            return

        self.p.set_data(event.xdata, event.ydata)

        if self.rectdict['round_to_int']:
            self.p_round.set_data(round(event.xdata), round(event.ydata))

        plt.draw()

    """
    Load a saved mission onto the map.
    """
    def set_plot(self, plot):
        self.rectdict['points'] = plot
        self.l.set_visible(True)
        self.l.set_data(list(zip(*self.rectdict['points'])))
        plt.draw()

    """
    Add a waypoint to the grid.
    """
    def add_point(self, x, y):
        self.rectdict['points'] += [[x, y]]

    """
    Remove waypoint from the grid.
    """
    def remove_point(self):
        self.rectdict['points'] = self.rectdict['points'][:-1]

    """
    Clear all waypoints from the plot.
    """
    def clear_plot(self):
        self.rectdict['points'] = []
        self.l.set_visible(False)
        plt.draw()

    """
    Change background blueprint image.
    """
    def change_image(self, path):
        self.current_path = path
        img = plt.imread(path)
        self.ax.imshow(img, extent=[0, self.x, self.y, 0], alpha=1)
        plt.draw()

    """
    Remove background image.
    """
    def set_blank(self, show):
        if show:
            img = plt.imread(self.current_path)
            self.ax.imshow(img, extent=[0, self.x, self.y, 0], alpha=1)
            plt.draw()
        else:
            img = plt.imread("images/blank.png")
            self.ax.imshow(img, extent=[0, self.x, self.y, 0], alpha=1)
            plt.draw()

    """
    Make waypoints snap to the grid.
    """
    def set_snap(self, snap):
        self.rectdict['round_to_int'] = snap

    """
    Increase size of plot.
    """
    def increase_size(self):
        self.h = self.h * 1.25
        self.w = self.w * 1.25
        self.f.set_size_inches(self.w, self.h)
        plt.draw()

    """
    Decrease size of plot.
    """
    def decrease_size(self):
        self.h = self.h / 1.25
        self.w = self.w / 1.25
        self.f.set_size_inches(self.w, self.h)
        plt.draw()


"""
Embed in a QWidget for addition to Application.
"""
class GridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.chart = Grid(self)
