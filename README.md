# Overview

MissionPlanner Desktop Application and MAVSDK drone communication software for MultiDrone project: a self-proposed MEng group project completed at University of Strathclyde.



# MultiDrone

MultiDrone is a proof-of-concept multi-purpose autonomous drone platform with a standardized modular mounting system designed to allow users to easily swap out different module payloads to deploy their drone for various different operations – e.g., payload delivery, crop spraying, 3D mapping etc. This concept means that drone operators could buy one drone and use it for multiple applications. It equally acts as a hardware and software platform for future application development with the advantage that developers with a new drone application idea would only have to design a module instead of building a new custom drone from the ground up.



# MultiDrone Mission Planner

This repository contains the Python source code for the MultiDrone Mission Planner application – a custom, cross-platform Ground Control Station software that allows users to plan both indoor and outdoor autonomous missions with connected module control and run them on a connected drone. The application is written in Python using PyQt for front-end GUI and business logic and drone communication functions using the MAVSDK Python library.

Outdoor mission planning screen:

<img width="1392" alt="Screen Shot 2022-04-25 at 12 55 13 AM" src="https://user-images.githubusercontent.com/78596856/165165766-f4410b07-fd0d-42e2-a46e-95d43430c243.png">

Indoor mission planning screen:

<img width="1392" alt="Screen Shot 2022-04-24 at 11 07 44 PM" src="https://user-images.githubusercontent.com/78596856/165165839-0d76fa5c-07d6-4db7-97a6-bd55e7ead7c8.png">


# Dependencies

The application has several library dependencies that should be installed before running. These can be installed using the 'pip install' command in the terminal. All required libraries are listed below. 

      PyQt5, PyQtWebEngine, mavsdk, folium, geocoder, asyncio, matplotlib,  json
      


Individual commands for quick access:
      
      pip install PyQt5

      pip install PyQtWebEngine

      pip install mavsdk

      pip install folium

      pip install geocoder

      pip install matplotlib

      pip install json



# Running Instructions

For best performance and to ensure that the application can access all the required dependencies, the MultiDrone Mission Planner application should be run from the terminal.

The entry point to the application is Main.py so simply navigate to the directory that the repository is cloned/downloaded and run:

      python Main.py

To connect to a SITL drone, the connection address in DroneFunctions can be kept the same. To connect to a real drone, the address variable should be changed to the serial port that your telemetry module is connected to. 



# Architecture

High-level architecture diagram for the software is provided below:


<img width="929" alt="Screen Shot 2022-04-25 at 9 14 10 PM" src="https://user-images.githubusercontent.com/78596856/165167806-b8b0f9e6-fdc5-4d75-b242-3401ef08df97.png">
