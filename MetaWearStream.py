# usage: python3 myStreamingExample.py [mac]

from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp, create_voidp_int
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange


class State:
    # init
    def __init__(self, device):
        self.device = device
        self.accsamples = 0
        self.gyrosamples = 0
        self.magsamples = 0
        self.tempsamples = 0
        self.presssamples = 0
        self.accCallback = FnVoid_VoidP_DataP(self.acc_data_handler)
        self.gyroCallback = FnVoid_VoidP_DataP(self.gyro_data_handler)
        self.magCallback = FnVoid_VoidP_DataP(self.mag_data_handler)
        self.tempCallback = FnVoid_VoidP_DataP(self.temp_data_handler)
        self.pressCallback = FnVoid_VoidP_DataP(self.press_data_handler)

    # acc callback
    def acc_data_handler(self, ctx, data):
        print("ACC: %s -> %s" % (self.device.address, parse_value(data)))
        self.accsamples+= 1

    # gyro callback
    def gyro_data_handler(self, ctx, data):
        print("GYRO: %s -> %s" % (self.device.address, parse_value(data)))
        self.gyrosamples+= 1

    # mag callback
    def mag_data_handler(self, ctx, data):
        print("MAG: %s -> %s" % (self.device.address, parse_value(data)))
        self.magsamples+= 1

    #temp callback
    def temp_data_handler(self, ctx, data):
        print("TEMP: %s -> %s" % (self.device.address, parse_value(data)))
        self.tempsamples += 1

    #pressure callback
    def press_data_handler(self, ctx, data):
        print("PRESS: %s -> %s" % (self.device.address, parse_value(data)))
        self.presssamples += 1

states = []

# connect to MetaWear, then add the device to the State queue.
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
    states.append(State(d))
    e = Event()

# configure
for s in states:
    print("Configuring device")
    #This API call configures, for the device in argument #1, min, max connection interval, latency and timeout.
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    # setup acc
    #Set output data rate for the Bosch sensor. Only some values are allowed and defined in the .h
    libmetawear.mbl_mw_acc_bmi270_set_odr(s.device.board, AccBmi270Odr._100Hz) # BMI 270 specific call
    #Set the range for the Bosch sensor. Default value to 0-4g.
    libmetawear.mbl_mw_acc_bosch_set_range(s.device.board, AccBoschRange._4G)
    #Applies ODR and Range to the sensor.
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

    # setup gyro
    #Same API calls as before.
    libmetawear.mbl_mw_gyro_bmi270_set_range(s.device.board, GyroBoschRange._1000dps);
    libmetawear.mbl_mw_gyro_bmi270_set_odr(s.device.board, GyroBoschOdr._100Hz);
    libmetawear.mbl_mw_gyro_bmi270_write_config(s.device.board);
    
    #setup pressure
    libmetawear.mbl_mw_baro_bosch_set_oversampling(s.device.board, BaroBoschOversampling.LOW_POWER)
    libmetawear.mbl_mw_baro_bmp280_set_standby_time(s.device.board, BaroBmp280StandbyTime._1000ms)
    libmetawear.mbl_mw_baro_bosch_set_iir_filter(s.device.board, BaroBoschIirFilter.AVG_16)
    libmetawear.mbl_mw_baro_bosch_write_config(s.device.board)
     
    # setup mag
    #Stop the magnetometer
    libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
    #Sets the power mode to one of the recommended presets. High Accuracy is 20Hz and consumes a lot, REGULAR is 10Hz and is nice to the battery.acc
    libmetawear.mbl_mw_mag_bmm150_set_preset(s.device.board, MagBmm150Preset.HIGH_ACCURACY)

    # get temp and subscribe
    signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(s.device.board, MetaWearRProChannel.ON_BOARD_THERMISTOR)
    libmetawear.mbl_mw_datasignal_subscribe(signal, None, s.tempCallback)
    #Create a timer that fires every 1s
    timer = create_voidp(lambda fn: libmetawear.mbl_mw_timer_create_indefinite(s.device.board, 1000, 0, None, fn), resource = "timer", event = e)
    #Create event based on timer: read temperature when timer fires
    libmetawear.mbl_mw_event_record_commands(timer)
    libmetawear.mbl_mw_datasignal_read(signal)
    create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(timer, None, fn), event = e)

    # get acc and subscribe
    #Get the data signal representing acceleration data
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    #And subscribe, defining the callback function to be called.
    libmetawear.mbl_mw_datasignal_subscribe(acc, None, s.accCallback)

    # get gyro and subscribe
    #Same as before.
    gyro = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(gyro, None, s.gyroCallback)

    # get mag and subscribe
    mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(mag, None, s.magCallback)
    
    #get press and subscribe
    pa_data_signal = libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(pa_data_signal, None, s.pressCallback)

    # start acc
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_start(s.device.board)

    # start gyro
    libmetawear.mbl_mw_gyro_bmi270_enable_rotation_sampling(s.device.board)
    libmetawear.mbl_mw_gyro_bmi270_start(s.device.board)

    # start mag
    libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_start(s.device.board)
    
    #start press
    libmetawear.mbl_mw_baro_bosch_start(s.device.board)

    # start temperature timer
    libmetawear.mbl_mw_timer_start(timer)

# sleep
sleep(10.0)

# stop
for s in states:
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

    libmetawear.mbl_mw_gyro_bmi270_stop(s.device.board)
    libmetawear.mbl_mw_gyro_bmi270_disable_rotation_sampling(s.device.board)

    libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(s.device.board)

    mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(mag)

    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(acc)

    gyro = libmetawear.mbl_mw_gyro_bmi270_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(gyro)

    #remove timer, event and unsubscribe
    libmetawear.mbl_mw_timer_remove(timer)
    sleep(1.0)

    libmetawear.mbl_mw_event_remove_all(s.device.board)
    sleep(1.0)

    libmetawear.mbl_mw_datasignal_unsubscribe(signal)
    sleep(2.0)

    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# recap
print("Total Samples Received")
for s in states:
    print("ACC -> %d" % (s.accsamples))
    print("GYR -> %d" % ( s.gyrosamples))
    print("MAG -> %d" % (s.magsamples))
    print("TEMP -> %d" % (s.tempsamples))
    print("PRESS -> %d" % (s.presssamples))
    

