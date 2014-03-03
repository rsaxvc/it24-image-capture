#!/usr/bin/python

#get all the arguments with argparse
import argparse
parser = argparse.ArgumentParser(description='IT-24 Image Capture Tool')
parser.add_argument("--port", help="Port name(example:COMA,COM1,/dev/ttyUSB0)")
#parser.add_argument("--parity", help="none,even,odd")
parser.add_argument("--outputtype", help="png or jpg")
args = parser.parse_args()

if not args.port:
	args.port = "/dev/ttyUSB0"

if not args.outputtype:
	args.outputtype = "png"

import serial

ser = serial.Serial(args.port, "115200", parity=serial.PARITY_NONE)

class State():
	hosed = 0
	newline = 1
	carriage = 2
	screencomp = 3
	width = 4
	height = 5
	data = 6

def charIsInt(c):
	if( ord(c) >= ord('0') and ord(c) <= ord('9') ):
		return True
	return False

def parseRLE( ser, width, height ):
	pixels = list()
	numPixels = 0
	numLoops = 0
	totalPixels = width*height
	while( numPixels < totalPixels ):
		pxl1=ser.read()
		pxl2=ser.read()
		count=ser.read()
		numPixels += ord(count)
		numLoops += 1
	return pixels

state = State.hosed
while True:
	if( state == State.hosed ):
		width = 0
		height = 0
	byte = bytearray(ser.read(1))[0]
	if( state == State.hosed ):
		if( byte == 0xD ):
			state = State.newline
		else:
			state = State.hosed
	elif( state == State.newline ):
		if( byte == 0xA ):
			state = State.carriage
			buf = ser.read(10)
			if( buf == "screencomp" ):
				print "Fetching Image..."
				state = State.screencomp
				while( True ):
					byte = ser.read(1)
					if( charIsInt( byte ) ):
						width = width * 10 + int( byte );
					elif( byte == 'x' ):
						state = State.width
						break
					else:
						state = State.hosed
						break
				print "\tWidth=",width
				while( True ):
					byte = ser.read(1)
					if( charIsInt( byte ) ):
						height = height * 10 + int( byte );
					elif( byte == ':' ):
						state = State.height
						break
					else:
						state = State.hosed
						break
				print "\tHeight=",height
			else:
				state = State.hosed
		else:
			state = State.hosed
	elif( state == State.height ):
		if( byte == ord(' ') ):
			state = State.data
			pixels = parseRLE( ser, width, height )
			ser.read(2)
			state = State.hosed
		else:
			state = State.hosed

ser.close()             # close port
