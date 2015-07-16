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

os.system('clear')

rangefinder = None # global variable.
DEVICE_CMD_RANGE_NOW = 0x51


class rangeFinder():
	def __init__(self, bus = 1, deviceaddress = 0x70, intpin = 23, verbose = 0):
	 self.bus = smbus.SMBus(bus)
	 self.deviceaddress = deviceaddress
	 self.intpin = intpin

	 GPIO.setmode( GPIO.BCM)
	 GPIO.setup( intpin, GPIO.IN, pull_up_down=GPIO.PUD_UP )

	 self.range = -1
	 self.verbose = verbose


	def next(self):
	 #get new range reading
	 valid = 0
	 data = [0,0]
 
	 #wait for status pin to pull port 23 low
	 try:
		 #wait for intpin to be ready 
		 self.bus.write_byte( self.deviceaddress,DEVICE_CMD_RANGE_NOW)
		 time.sleep( 0.05 ) # give it a chance to start ranging 
		 #GPIO.wait_for_edge( self.intpin, GPIO.FALLING ) #wait for it to signal ranging finished
		 #^is causing an error
		 #time.sleep( 1 )
		 data = self.bus.read_i2c_block_data( self.deviceaddress , 0, 2 )
		 #^this is not always reading both bytes well.
		 #v1[0] = self.bus.read_byte(self.deviceaddress)
		 time.sleep(0.05)
		 valid = 1
		 #v1[1] = self.bus.read_byte(self.deviceaddress)
	 	 if self.verbose > 0:
	  	  sys.stderr.write(' highbyte = {0:b} , lowbyte = {1:b},'.format(data[0], data[1]) )
	 except IOError as e:
	         repr( e )
		 print "I/O error({0}): {1}".format(e.errno, e.strerror)
		 valid = 0
		 #need to recover I2C bus state.
		 
		 

	 except KeyboardInterrupt as e:
		 repr( e )
		 #need some connection monitoring on IOError?
		 GPIO.cleanup()	#cleanup GPIO on Ctrl-C exit
		 valid = 0

	 if (valid == 1):
	 	 #format highbyte
		 highbyte = data[0] #maxbotix sends signed 8bit int high byte
		 #highbyte = highbyte & 0x7f #drop the sign bit
		 lowbyte = data[1] #maxbotix sends unsigned 8bit int low byte
		 #assemble 16bit value
		 self.range = (highbyte<<8) + lowbyte
	 else:
		 self.range = -1
		

	 #write high and low bytes out to std err for debugging
	 if self.verbose > 0:
	  sys.stderr.write(' range = {}\r\n'.format(self.range) )

	 return self.range

class RangeFinderPoller(threading.Thread):
	def __init__(self):
	 threading.Thread.__init__(self)
	 global rangefinder #bring it in scope
	 rangefinder = rangeFinder(1, 0x70, 23, 1)
	 self.current_value = None
	 self.running = True

	def run(self):
	 global rangefinder
	 while self.running:
	  rangefinder.next()


if __name__ == "__main__":

 os.chdir('/var/www/logs')

 rfp = RangeFinderPoller()
 try:
  unitname = os.uname()[1]
  starttime = time.strftime("%Y%m%d-%H%M%S")
  filename = unitname + '_' + starttime + '_log_range.csv'
  bufsize = 1
  fid = io.open(filename,'w',bufsize)
  header = u"utc_seconds, range (cm)\r\n"
  fid.write(header)
  rfp.start()
  while True:
   #
   os.system('clear')
   
   fid.write(u"{:f}, {}\r\n".format(
				time.time(),
				rangefinder.range,
				))

   print 'time: {}' , time.time()
   print 'range: {}' , rangefinder.range

   time.sleep(0.1)

 except (KeyboardInterrupt, SystemExit):
  fid.close()
  print "\nKilling Thread..."
  rfp.running = False
  rfp.join() # wait for the thread to finish what it's doing
  GPIO.cleanup()
  exit()
	
