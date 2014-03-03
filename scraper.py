#!/usr/bin/python

#get all the arguments with argparse
import argparse
from PIL import Image

parser = argparse.ArgumentParser(description='IT-24 Image Capture Tool')
parser.add_argument("--port", help="Port name(example:COMA,COM1,/dev/ttyUSB0)")
parser.add_argument("--prefix", help="Prepend this pattern in front of the captures")
parser.add_argument("--outputtype", help="png or jpg")
args = parser.parse_args()

if not args.port:
	args.port = "/dev/ttyUSB0"

if not args.outputtype:
	args.outputtype = "png"

if not args.prefix:
	args.prefix = ""

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

def RGB565_to_RGB888( pixel ):
	red   = ((pixel & 0xf800) >> 11)<<3
	red  |= red >> 5
	green = ((pixel & 0x07e0) >>  5)<<2
	green|= green >> 5
	blue   = ((pixel & 0x001f) >>  0)<<3
	blue |= blue >> 5
	return (red,green,blue)

def parseRLE( ser, width, height ):
	pixels = list()
	numPixels = 0
	numLoops = 0
	totalPixels = width*height
	while( numPixels < totalPixels ):
		pxl1=ord(ser.read())
		pxl2=ord(ser.read())
		pxl = RGB565_to_RGB888( ( pxl1 << 8 ) | pxl2 )
		count=ord(ser.read())
		for i in xrange(0,count):
			pixels.append(pxl)
		numPixels += count
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
			im = Image.new("RGB", (width, height))
			im.putdata(pixels)
			im.save(args.prefix+"output."+args.outputtype)
			state = State.hosed
		else:
			state = State.hosed

ser.close()             # close port
