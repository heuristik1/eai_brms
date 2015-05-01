#Pi Temp Logger
#Ashconllc
#04/15/15
#v1.0

import smbus
import time
import datetime

bus = smbus.SMBus(1)

#I2C address of Sensors
address = 0x4c
mode = 0x5d


try:
  r1 = bus.read_byte_data(address, 0x01)     # Retrieve current mode select
  if r1 != mode:                             # If current mode != R1
    bus.write_byte_data(address, 0x01, mode) # Initializes the IC

except IOError, err:
  print err

bus.write_byte_data(address, 0x02, 0x00) # Trigger a data collection

r0 = bus.read_byte_data(address, 0x00) # Status
r1 = bus.read_byte_data(address, 0x01) # Control - mode select
r4 = bus.read_byte_data(address, 0x04) # Temp. Int. MSB
r5 = bus.read_byte_data(address, 0x05) # Temp. Int. LSB
r6 = bus.read_byte_data(address, 0x06) # V1, V1 - V2 or TR1 MSB
r7 = bus.read_byte_data(address, 0x07) # V1, V1 - V2 or TR1 LSB
r8 = bus.read_byte_data(address, 0x08) # V2, V1 - V2 or TR1 MSB
r9 = bus.read_byte_data(address, 0x09) # V2, V1 - V2 or TR1 LSB
ra = bus.read_byte_data(address, 0x0a) # V3, V3 - V4 or TR2 MSB
rb = bus.read_byte_data(address, 0x0b) # V3, V3 - V4 or TR2 LSB
rc = bus.read_byte_data(address, 0x0c) # V4, V3 - V4 or TR2 MSB
rd = bus.read_byte_data(address, 0x0d) # V4, V3 - V4 or TR2 LSB
re = bus.read_byte_data(address, 0x0e) # Vcc MSB
rf = bus.read_byte_data(address, 0x0f) # Vcc LSB

def temperatureTr1():
	rvalue0 = bus.read_word_data(address,0)
	rvalue1 = (rvalue0 & 0xff00) >> 8
	rvalue2 = rvalue0 & 0x00ff
	rvalue = (((rvalue2 * 256) + rvalue1) >> 4) *.0625
	return rvalue
def temperatureTr2():
	rvalue0 = bus.read_word_data(address,0)
	rvalue1 = (rvalue0 & 0xff00) >> 8
	rvalue2 = rvalue0 & 0x00ff
	rvalue = (((rvalue2 * 256) + rvalue1) >> 4) *.0625
	return rvalue

while True:

	#Open Log File
	f=open('Tempdata.txt','a')
	now = datetime.datetime.now()
	timestamp = now.strftime("%Y/%m/%d %H:%M:%S")
	outvalue = temperatureTr1
	outstring = str(timestamp)+" "+str(outvalue)
	print outstring
	f.write(outstring)
	f.close()

	#log temp every 1 second
	time.sleep(1)

