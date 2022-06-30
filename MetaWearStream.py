# usage: python3 MetaWearStream.py

from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp, create_voidp_int
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys
import re
import os

# -------------------------------------------------------------------------------
#
#	VARIABLES TO SETUP FOR CONNECTION :)
#
# -------------------------------------------------------------------------------


device_name = " " 
metamotion_mac_address = " "
bluetooth_adapter_mac_address = " "
sampling_time = 2.0


if(metamotion_mac_address == " " or bluetooth_adapter_mac_address == " " or device_name == " "):
	print("You did not setup the script for connection. \nPlease open the .py file and compile the mac address variables!")
	exit()


if sys.version_info[0] == 2:
    range = xrange
    
# acc callback
def acc_data_handler(ctx, data):
	global d, accsamples, accFile, r
	#print("ACC: %s -> %s" % (d.address, parse_value(data)))
	axisValues = r.findall(str(parse_value(data)))  
	accFile.write("%d,%s,%s,%s\n" % (data.contents.epoch, axisValues[0],  axisValues[1],  axisValues[2]))
	accsamples += 1

# gyro callback
def gyro_data_handler(ctx, data):
	global d, gyrosamples, gyroFile
	#print("GYRO: %s -> %s" % (d.address, parse_value(data)))
	axisValues = r.findall(str(parse_value(data)))  
	gyroFile.write("%d,%s,%s,%s\n" % (data.contents.epoch, axisValues[0],  axisValues[1],  axisValues[2]))
	gyrosamples += 1

# mag callback
def mag_data_handler(ctx, data):
	global d, magsamples, magFile
	#print("MAG: %s -> %s" % (d.address, parse_value(data)))
	axisValues = r.findall(str(parse_value(data)))  
	magFile.write("%d,%s,%s,%s\n" % (data.contents.epoch, axisValues[0],  axisValues[1],  axisValues[2]))
	magsamples += 1

#temp callback
def temp_data_handler(ctx, data):
	global d, tempsamples, tempFile
	#print("TEMP: %s -> %s" % (d.address, parse_value(data)))
	tempFile.write("%d,%s\n" % (data.contents.epoch, parse_value(data)))
	tempsamples += 1

#pressure callback
def press_data_handler(ctx, data):
	global d, presssamples, pressFile
	#print("PRESS: %s -> %s" % (d.address, parse_value(data)))
	pressFile.write("%d,%s\n" % (data.contents.epoch, parse_value(data)))
	presssamples += 1

accsamples = 0
gyrosamples = 0
magsamples = 0
tempsamples = 0
presssamples = 0
accCallback = FnVoid_VoidP_DataP(acc_data_handler)
gyroCallback = FnVoid_VoidP_DataP(gyro_data_handler)
magCallback = FnVoid_VoidP_DataP(mag_data_handler)
tempCallback = FnVoid_VoidP_DataP(temp_data_handler)
pressCallback = FnVoid_VoidP_DataP(press_data_handler)

# create files
filename = "output/acc_" + device_name + ".csv"
os.makedirs(os.path.dirname(filename), exist_ok=True)
accFile = open(filename, "w")
accFile.write("epoch,valueX,valueY,valueZ\n")

filename = "output/gyro_" + device_name + ".csv"
gyroFile = open(filename, "w")
gyroFile.write("epoch,valueX,valueY,valueZ\n")

filename = "output/mag_" + device_name + ".csv"
magFile = open(filename, "w")
magFile.write("epoch,valueX,valueY,valueZ\n")

filename = "output/temp_" + device_name + ".csv"
tempFile = open(filename, "w")
tempFile.write("epoch,value\n")

filename = "output/press" + device_name + ".csv"
pressFile = open(filename, "w")
pressFile.write("epoch,value\n") 

# define a regular expression to take axes from the output - will match all floats
r = re.compile("[+-]?[0-9]*[.][0-9]+")

# connect to the MetaWear sensor, using the address specified before

d = MetaWear(metamotion_mac_address, hci_mac = bluetooth_adapter_mac_address)
d.connect()
print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
e = Event()

# configure

#This API call configures, for the device in argument #1, min, max connection interval, latency and timeout.
libmetawear.mbl_mw_settings_set_connection_parameters(d.board, 7.5, 7.5, 0, 6000)
sleep(1.5)

# setup acc
#Set output data rate for the Bosch sensor. Only some values are allowed and defined in the .h
libmetawear.mbl_mw_acc_bmi270_set_odr(d.board, AccBmi270Odr._100Hz) # BMI 270 specific call
#Set the range for the Bosch sensor. Default value to 0-4g.
libmetawear.mbl_mw_acc_bosch_set_range(d.board, AccBoschRange._4G)
#Applies ODR and Range to the sensor.
libmetawear.mbl_mw_acc_write_acceleration_config(d.board)

# setup gyro
#Same API calls as before.
libmetawear.mbl_mw_gyro_bmi270_set_range(d.board, GyroBoschRange._1000dps);
libmetawear.mbl_mw_gyro_bmi270_set_odr(d.board, GyroBoschOdr._100Hz);
libmetawear.mbl_mw_gyro_bmi270_write_config(d.board);
    
#setup pressure
libmetawear.mbl_mw_baro_bosch_set_oversampling(d.board, BaroBoschOversampling.LOW_POWER)
libmetawear.mbl_mw_baro_bmp280_set_standby_time(d.board, BaroBmp280StandbyTime._1000ms)
libmetawear.mbl_mw_baro_bosch_set_iir_filter(d.board, BaroBoschIirFilter.AVG_16)
libmetawear.mbl_mw_baro_bosch_write_config(d.board)
     
# setup mag
#Stop the magnetometer
libmetawear.mbl_mw_mag_bmm150_stop(d.board)
#Sets the power mode to one of the recommended presets. High Accuracy is 20Hz and consumes a lot, REGULAR is 10Hz and is nice to the battery.acc
libmetawear.mbl_mw_mag_bmm150_set_preset(d.board, MagBmm150Preset.HIGH_ACCURACY)

# get temp and subscribe
signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(d.board, MetaWearRProChannel.ON_BOARD_THERMISTOR)
libmetawear.mbl_mw_datasignal_subscribe(signal, None, tempCallback)
#Create a timer that fires every 1s
timer = create_voidp(lambda fn: libmetawear.mbl_mw_timer_create_indefinite(d.board, 1000, 0, None, fn), resource = "timer", event = e)
#Create event based on timer: read temperature when timer fires
libmetawear.mbl_mw_event_record_commands(timer)
libmetawear.mbl_mw_datasignal_read(signal)
create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(timer, None, fn), event = e)

# get acc and subscribe
#Get the data signal representing acceleration data
acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(d.board)
#And subscribe, defining the callback function to be called.
libmetawear.mbl_mw_datasignal_subscribe(acc, None, accCallback)

# get gyro and subscribe
#Same as before.
gyro = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(d.board)
libmetawear.mbl_mw_datasignal_subscribe(gyro, None, gyroCallback)

# get mag and subscribe
mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(d.board)
libmetawear.mbl_mw_datasignal_subscribe(mag, None, magCallback)
    
#get press and subscribe
pa_data_signal = libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(d.board)
libmetawear.mbl_mw_datasignal_subscribe(pa_data_signal, None, pressCallback)

# start acc
libmetawear.mbl_mw_acc_enable_acceleration_sampling(d.board)
libmetawear.mbl_mw_acc_start(d.board)

# start gyro
libmetawear.mbl_mw_gyro_bmi270_enable_rotation_sampling(d.board)
libmetawear.mbl_mw_gyro_bmi270_start(d.board)

# start mag
libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(d.board)
libmetawear.mbl_mw_mag_bmm150_start(d.board)
    
#start press
libmetawear.mbl_mw_baro_bosch_start(d.board)

# start temperature timer
libmetawear.mbl_mw_timer_start(timer)

# sleep
sleep(sampling_time)

# stop

libmetawear.mbl_mw_acc_stop(d.board)
libmetawear.mbl_mw_acc_disable_acceleration_sampling(d.board)

libmetawear.mbl_mw_gyro_bmi270_stop(d.board)
libmetawear.mbl_mw_gyro_bmi270_disable_rotation_sampling(d.board)

libmetawear.mbl_mw_mag_bmm150_stop(d.board)
libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(d.board)

libmetawear.mbl_mw_baro_bosch_stop(d.board)

mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(d.board)
libmetawear.mbl_mw_datasignal_unsubscribe(mag)

acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(d.board)
libmetawear.mbl_mw_datasignal_unsubscribe(acc)

gyro = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(d.board)
libmetawear.mbl_mw_datasignal_unsubscribe(gyro)

press =  libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(d.board)
libmetawear.mbl_mw_datasignal_unsubscribe(press)

#remove timer, event and unsubscribe
libmetawear.mbl_mw_timer_remove(timer)
sleep(1.0)

libmetawear.mbl_mw_event_remove_all(d.board)
sleep(1.0)

libmetawear.mbl_mw_datasignal_unsubscribe(signal)
sleep(2.0)

libmetawear.mbl_mw_debug_disconnect(d.board)

# recap
print("Total Samples Received")
print("ACC -> %d" % (accsamples))
print("GYR -> %d" % (gyrosamples))
print("MAG -> %d" % (magsamples))
print("TEMP -> %d" % (tempsamples))
print("PRESS -> %d" % (presssamples))
    

