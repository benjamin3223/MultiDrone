#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 27 12:16:34 2022

@author: Benjamin
"""

import asyncio

from mavsdk import System
from mavsdk.telemetry import (PositionNed)
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from mavsdk.mission import (MissionItem, MissionPlan)


address = "udp://:14540"           # For SITL testing.
# address = "serial://COM6:56000"  # Uncomment for use with real drone and USB telemetry module


async def connect():

    drone = System()

    await drone.connect(system_address=address)
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            # return True
            break
        
    return True


async def run_indoor(mission):

    drone = System()
    attempts = 0
    mission_point = mission

    print("Mission Started")
    await drone.connect(system_address=address)
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break
        asyncio.sleep(1)
        attempts += 1
        if attempts > 10:
            return False

    print("-- Arming")
    await drone.action.arm()
    async for is_armed in drone.telemetry.armed():
        if is_armed is True:
            print("The drone is armed ")
            break

    print("-- Setting initial setpoint")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: {error._result.result}")
        print("-- Disarming")
        await drone.action.disarm()
        return
    for i in range(0, len(mission_point)):
        print(f"-- Go {mission_point[i][0]}m North, {mission_point[i][1]}m East, {mission_point[i][2]}m Down within local coordinate system")
        await drone.offboard.set_position_ned(PositionNedYaw(mission_point[i][0],mission_point[i][1],mission_point[i][2],mission_point[i][3]))
        async for current_position in drone.telemetry.position_velocity_ned():
            print("north: ", current_position.position.north_m)
            print("east: ", current_position.position.east_m)
            print("down: ", current_position.position.down_m)
            if (current_position.position.north_m >= mission_point[i][0]) and (current_position.position.east_m >= mission_point[i][1]) and (current_position.position.down_m <= mission_point[i][2]):
                print("Waypoint was reached")
                break
        print("Next waypoint")
    print ("Flying back to starting position")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
    async for current_position in drone.telemetry.position_velocity_ned():
        if ((current_position.position.north_m >= 0.0) and (
                current_position.position.east_m >= 0.0) and (
                current_position.position.down_m <= 0.0)):
            print("Waypoint was reached")
            break
    await drone.action.land()
    await drone.action.disarm()


async def run_outdoor(mission, telemetry, ret):
    
    drone = System()
    attempts = 0
    await drone.connect(system_address=address)  # CHANGE

    # asyncio.ensure_future(print_battery(drone, telemetry))
    # # asyncio.ensure_future(print_gps_info(drone, result))
    # asyncio.ensure_future(print_in_air(drone, telemetry))
    # asyncio.ensure_future(print_position(drone, telemetry))

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break
        asyncio.sleep(1)
        attempts += 1
        if attempts > 10:
            return False

    print_mission_progress_task = asyncio.ensure_future(
        print_mission_progress(drone))

    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(
        observe_is_in_air(drone, running_tasks))

    mission_items = []
    for waypoint in mission:

        if address == "udp://:14540":
            mission_items.append(MissionItem(waypoint[0],
                                             waypoint[1],
                                             waypoint[2],
                                             1,
                                             True,
                                             float('nan'),
                                             float('nan'),
                                             MissionItem.CameraAction.NONE,
                                             float('nan'),
                                             float('nan'),
                                             float('nan'),
                                             float('nan')))
        else:
            mission_items.append(MissionItem(waypoint[0],
                                             waypoint[1],
                                             waypoint[2],
                                             1,
                                             True,
                                             float('nan'),
                                             float('nan'),
                                             MissionItem.CameraAction.NONE,
                                             float('nan'),
                                             float('nan'),
                                             float('nan'),
                                             float('nan'),
                                             float('nan')))

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(ret)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("-- Arming")
    await drone.action.arm()
    async for is_armed in drone.telemetry.armed():
        if is_armed is True:
            print("The drone is armed ")
            break

    print("-- Starting mission")
    await drone.mission.start_mission()

    await termination_task


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")


async def observe_is_in_air(drone, running_tasks):
    """ Monitors whether the drone is flying or not and
    returns after landing """
    was_in_air = False

    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air

        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()

            return


async def get_telemetry(result, outdoor):
    # Init the drone
    drone = System()
    attempts = 0
    await drone.connect(system_address=address)
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break
        asyncio.sleep(1)
        attempts += 1
        if attempts > 10:
            return False

    # Start the tasks
    asyncio.ensure_future(print_battery(drone, result))
    # asyncio.ensure_future(print_gps_info(drone, result))
    asyncio.ensure_future(print_in_air(drone, result))
    if outdoor:
        asyncio.ensure_future(print_position(drone, result))


async def get_battery(result):
    
    drone = System()
    
    await drone.connect(system_address=address)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break
    
    async for battery in drone.telemetry.battery():
        print(battery.remaining_percent)
        result[0] = battery.remaining_percent
        break
    
    # return battery.remaining_percent


async def get_gps_info(drone):
    async for gps_info in drone.telemetry.gps_info():
        return gps_info


async def get_in_air(drone):
    async for in_air in drone.telemetry.in_air():
        return in_air


async def get_position(drone):
    async for position in drone.telemetry.position():
        return position


async def print_telemetry():
    # Init the drone
    drone = System()
    await drone.connect(system_address=address)

    # Start the tasks
    asyncio.ensure_future(print_battery(drone))
    asyncio.ensure_future(print_gps_info(drone))
    asyncio.ensure_future(print_in_air(drone))
    asyncio.ensure_future(print_position(drone))


async def print_battery(drone, result):
    async for battery in drone.telemetry.battery():
        print(f"Battery: {battery.remaining_percent}")
        result[0] = battery.remaining_percent
        await asyncio.sleep(5)
        # break


async def print_gps_info(drone, result):
    async for gps_info in drone.telemetry.gps_info():
        print(f"GPS info: {gps_info}")
        await asyncio.sleep(5)
        # break


async def print_in_air(drone, result):
    async for in_air in drone.telemetry.in_air():
        print(f"In air: {in_air}")
        result[1] = in_air
        await asyncio.sleep(5)
        # break


async def print_position(drone, result):
    async for position in drone.telemetry.position():
        print(position)
        result[2] = position
        await asyncio.sleep(5)
        # break
