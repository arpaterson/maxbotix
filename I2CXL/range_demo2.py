#!/usr/bin/python
#
# Author: Anthony Paterson, May 2015, arpaterson.wordpress.com

import os, sys
import io
import threading
import smbus
import time
import RPi.GPIO as GPIO
import struct

DEVICE_CMD_RANGE_NOW = 0x51

os.system('clear')

class reading():
	def __init__(self):
	 self.val = -1
	 self.time = -1
	 self.valid = 0

class mbxi2c():
	######################################################
	def __init__(self, i2cbus, deviceaddress, intpin, verbose):
	 self.verbose = verbose
	 self.range = reading()

	 self.deviceaddress = deviceaddress
	 self.intpin = intpin

	 self.bus = smbus.SMBus(i2cbus)
	 GPIO.setmode(GPIO.BCM)
	 GPIO.setup(self.intpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	 GPIO.add_event_detect(self.intpin, GPIO.FALLING, callback = self.mbx_ready_callback, bouncetime=25)

	######################################################
	def send_cmd(self,command):
	 self.bus.write_byte(self.deviceaddress,command)
	 time.sleep(0.02)

	######################################################
	def read_range(self):
	 data = self.bus.read_i2c_block_data(self.deviceaddress,0,2)
	 self.range.time = time.time()
	 time.sleep(0.02)

	 highbyte = data[0] #maxbotix sends signed 8bit int high byte
         highbyte = highbyte & 0x7f #drop the sign bit
         lowbyte = data[1] #maxbotix sends unsigned 8bit int low byte

	 self.range.val = (highbyte<<8) + lowbyte
	 sys.stderr.write("time: {} range: {}\n".format(self.range.time, self.range.val))

	######################################################
	def mbx_ready_callback(self,channel):
	 if self.verbose > 0:
	  sys.stderr.write("mbx_ready_callback:\n")
	 #Read last data
	 self.read_range()
	 time.sleep(0.025)
	 #Any delay needed?

	 #Send ranging command
	 self.send_cmd(DEVICE_CMD_RANGE_NOW)
	 time.sleep(0.025)

	######################################################
	def start(self):
	 self.send_cmd(DEVICE_CMD_RANGE_NOW)
	 time.sleep(0.025)
	######################################################



if __name__=="__main__":
 try:
  rf = mbxi2c(1,0x70, 23, 0);
  rf.start()
  while True:
   pass
   #print("time: {} range: {}\n".format(rf.range.time, rf.range.val))
   #time.sleep(0.02)

 except (KeyboardInterrupt, IOError, SystemExit):
  GPIO.cleanup()

	
