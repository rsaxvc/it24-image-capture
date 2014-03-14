#!/usr/bin/python

#get all the arguments with argparse
import argparse
from PIL import Image

parser = argparse.ArgumentParser(description='IT-24 Image Capture Tool')
parser.add_argument("--port", help="Port name(example:COMA,COM1,/dev/ttyUSB0)")
parser.add_argument("--prefix", help="Prepend this pattern in front of the captures")
parser.add_argument("--outputtype", help="png or jpg")
parser.add_argument("--baud", help="38400 for older units 115200(default) for IT-24")
args = parser.parse_args()

if not args.port:
	args.port = "/dev/ttyUSB0"

if not args.outputtype:
	args.outputtype = "png"

if not args.prefix:
	args.prefix = "image_"

if not args.baud:
	args.baud = "115200"

import serial

ser = serial.Serial(args.port, args.baud, parity=serial.PARITY_NONE)

def nextFilename():
	global args
	prepath = args.prefix
	postpath = "." + args.outputtype

	num = 0
	import os
	while( True ):
		path = prepath + str(num).zfill(4) + postpath
		while( os.path.exists( path ) ):
			num += 1
			path = prepath + str(num).zfill(4) + postpath
		yield path

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

def W1_to_RGB888( pixel ):
	if( pixel ):
		pixel = 0
	else:
		pixel = 0xFF
	return (pixel,pixel,pixel)

def parseRLE( ser, width, height ):
	pixels = list()
	numPixels = 0
	totalPixels = width*height
	while( numPixels < totalPixels ):
		pxl1=ord(ser.read())
		pxl2=ord(ser.read())
		pxl = RGB565_to_RGB888( ( pxl1 << 8 ) | pxl2 )
		count=ord(ser.read())
		for i in xrange(0,count):
			pixels.append(pxl)
		numPixels += count
	return pixels

def hexnib2int( ch ):
	if( ord(ch) >= ord('0') and ord(ch) <= ord('9') ):
		return ord(ch) - ord('0')
	elif ( ord(ch) >= ord('a') and ord(ch) <= ord('f') ):
		return 10 + ord(ch) - ord('a')
	elif ( ord(ch) >= ord('A') and ord(ch) <= ord('F') ):
		return 10 + ord(ch) - ord('A')

def parseBPP( ser, width, height ):
	pixels = [0]*(width*height)
	x = 0
	y = 0
	totalPixels = width*height
	for y in xrange(height - 1, -1, -1):
		for x in xrange(0,width/4):
			bits=hexnib2int(ser.read())
			pixels[ y * width + 4 * x + 3 ] = (W1_to_RGB888( bits & 1 ) )
			pixels[ y * width + 4 * x + 2 ] = (W1_to_RGB888( bits & 2 ) )
			pixels[ y * width + 4 * x + 1 ] = (W1_to_RGB888( bits & 4 ) )
			pixels[ y * width + 4 * x + 0 ] = (W1_to_RGB888( bits & 8 ) )
	return pixels

class Mode():
	Invalid = -1
	RLE565 = 0
	BitPerPixel = 1

class State():
	hosed = 0
	newline = 1
	carriage = 2
	screencomp = 3
	width = 4
	height = 5
	data = 6

state = State.hosed
filenames = nextFilename()

mode = Mode.Invalid
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
				mode = Mode.RLE565
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
			elif( buf =="screenshot" ):
				print "Fetching Image"
				mode = Mode.BitPerPixel
				state = State.screencomp
				width = 64
				height = 128
				byte = bytearray(ser.read(1))[0]
				if( byte == ord(':') ):
					state = State.height
				else:
					state = State.hosed
		else:
			state = State.hosed
	elif( state == State.height ):
		if( byte == ord(' ') ):
			state = State.data
			if( mode == Mode.RLE565 ):
				pixels = parseRLE( ser, width, height )
				ser.read(2)#eat a carriage-return and new-line
			elif( mode == Mode.BitPerPixel ):
				pixels = parseBPP( ser, width, height )
				print "parsedBPP"

				#consume extra lines of '0', and one carriage-return
				byte = '0'
				while byte == '0':
					byte = ser.read(1)

				#eat a new-line
				ser.read(1)
			else:
				print "Unknown image format"
			im = Image.new("RGB", (width, height))
			im.putdata(pixels)
			filename = filenames.next()
			if( mode == Mode.BitPerPixel ):
				im=im.rotate(270)
			im.save(filename)
			print "...saved to",filename
			state = State.hosed
		else:
			print "byte:",byte
			state = State.hosed

ser.close()             # close port
