# MetaMotionStream
A simple Python script used to stream sensor values from MetaMotion sensor boards and save them in .csv files.

[MBIENTLAB MetaMotion webpage](https://mbientlab.com/)

- Compatible with Linux machines
- Accelerometer and Gyroscope stream at 100Hz
- Magnetometer stream at 25Hz
- Temperature and pressure stream at 1Hz.
- You can choose the Bluetooth controller to be used. In this way you can launch more instances of the script, using multiple bluetooth dongles.  

## Usage
1. Install the Software Development Kit for Python from MBIENTLAB [following the instructions here.](https://github.com/mbientlab/MetaWear-SDK-Python) Remember to verify that all dependencies are satisfied before proceeding with the installation. 
2. Modify the Python script by adding, in the corresponding variables, the mac address of the MetaMotion device you want to connect to, the mac address of the bluetooth controller you want to use and a name for the device you are connecting to. You can obtain the mac address of the bluetooth controller(s) by typing in a terminal `bluetoothctl list` as root.
3. Run the script as `python3 MetaWearStream.py`. Only python3 is supported.
