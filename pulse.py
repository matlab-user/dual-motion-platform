#!/user/bin/env python

import RPi.GPIO as GPIO
import time

GPIO.setmode( GPIO.BOARD )
GPIO.setup( 11, GPIO.OUT )

loop = 0
sig = False
while True:
	GPIO.output( 11, sig )
	time.sleep( 1 )
	sig = not sig
	print sig, time.time()
	loop += 1
	if loop>10**1:
		break
		
GPIO.cleanup()