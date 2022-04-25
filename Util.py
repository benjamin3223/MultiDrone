"""

Python file for all the Util functions required by the Application.

"""


"""
Save the current mission planner state to a text file.
"""
def saveMission(name, offset, indoor, outdoor):
    path = "missions.txt"

    missionFile = open(path, 'a')
    missionFile.write(
        f"{name};")
    missionFile.write(
        f"{offset};")
    missionFile.write(
        f"{indoor};")
    missionFile.write(
        f"{outdoor};\n")
    missionFile.close()
    return


"""
Read all missions in the saved missions text file and return as dictionary.
"""
def readMissions():
    path = "missions.txt"

    missionFile = open(path, 'r')
    mission_str = missionFile.readlines()
    missions = {}

    for line in mission_str:
        variables = line.split(';')
        mission_name = variables[0].strip()
        offset_str = variables[1].replace(" ", "")
        offset_str = offset_str[1:-1]
        indoor_mission_str = variables[2].replace(" ", "")
        outdoor_mission_str = variables[3].replace(" ", "")

        offset_split = offset_str.split(',')
        offset = [float(offset_split[0]), float(offset_split[1])]
        indoor_mission = stringToArray(indoor_mission_str)
        outdoor_mission = stringToArray(outdoor_mission_str)
        missions[mission_name] = [offset, indoor_mission, outdoor_mission]

    missionFile.close()
    return missions


"""
Convert the string form of mission arrays to a Python list variable.
"""
def stringToArray(string):
    if string == '[]':
        return []

    string = string[1:-1]
    string = string.replace("[", "")
    string = string.replace("],", ";")
    string = string.replace("]", "")
    waypoints = string.split(';')
    array = []

    for wp in waypoints:
        if wp == waypoints[-1]:
            elem = wp.split(',')
        else:
            elem = wp.split(',')
        arr = []
        for e in elem:
            arr.append(float(e))
        array.append(arr)

    return array


"""
Apply saved offset for indoor mission to overall waypoints ready for plotting
on GridPlanner.
"""
def missionToPlot(mission, offset):
    plot = []
    for wp in mission:
        plot.append([wp[0] + offset[0], wp[1] + offset[1]])
    return plot


"""
Check altitude input for possible error handling.
"""
def checkAltitude(altitude):
    try:
        altitude_fl = float(altitude)
    except:
        return -1

    if 0.9 < altitude_fl < 25.1:
        return altitude_fl
    else:
        return 0


"""
Check speed input for possible error handling.
"""
def checkSpeed(speed):
    try:
        speed_fl = float(speed)
    except:
        return -1

    if 0.1 < speed_fl < 5.1:
        return speed_fl
    else:
        return 0


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


# Check and format input for adding waypoint.
def formatDimensions(dimensions_str):
    try:
        dimensions_arr = dimensions_str.split(',')
    except:
        print("split")
        return []

    n = len(dimensions_arr)
    if not n == 2:
        print("number")
        return []

    try:
        dimensions = [float(dimensions_arr[0]), float(dimensions_arr[1])]
    except:
        print("float")
        return []

    return dimensions


"""
Generate string from waypoint input to display on Terminal Planner.
"""
def terminalString(wp_arr, outdoor):
    if outdoor:
        wp_text = "\nNext waypoint co-ordinates:        N:" + str(wp_arr[0]) + "    W:" + str(wp_arr[1]) + "    Alt:" \
                  + str(wp_arr[2]) + "m \n"
    else:
        wp_text = "\nNext waypoint co-ordinates:        x = " + str(wp_arr[0]) + "m    y = " + str(wp_arr[1]) + \
                  "m    z = " + str(wp_arr[2]) + "m \n"

    return wp_text
