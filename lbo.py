#!/usr/bin/env python

import RPi.GPIO as GPIO
from time import sleep,time
from datetime import datetime
from subprocess import call
from threading import Thread

class lbo(object):
	def __init__(self,pin=26,grace=60,verb=True,callback=None,gracecb=None,cancelcb=None):
		self.pin=pin
		self.lbocb=callback
		self.gracecb=gracecb
		self.cancelcb=cancelcb
		self.verb=verb
		self.grace=grace
		self.keeprunning=True

		def nil(): return
		if self.lbocb is None:    self.lbocb=nil
		if self.gracecb is None:  self.gracecb=nil
		if self.cancelcb is None: self.cancelcb=nil

		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.pin, GPIO.IN)

		if self.verb:print("lbo: checking for low battery output signal from pin {p}, {t}".format(p=pin,t=datetime.now()))
		if not self.goodbat(): 
			m = "no battery reading, assuming on wall power. no low battery monitoring will occur. lbo exiting."
			if self.verb: print("lbo: {}".format(m))
			raise RuntimeError(m)

	def goodbat(self):
		# NOTE: dont pull pin up or down because built in resistor will have lower resistance than the one externally attached
		val = GPIO.input(self.pin)
		if self.verb: print("lbo: current LBO reading: {}".format(val))
		return bool(val)

	def start(self):
		self.t=Thread(target=self.run)
		self.t.start()

	def run(self, timeout=500):
		state = "running"
		start = None
		while self.keeprunning:
			if state == "pending":
				if time() - start > self.grace:
					if self.verb: print("lbo: grace time expired, executing lbo action")
					self.lbocb()
					state = "running" # if, for some reason, the cb is not a poweroff

                        f=GPIO.wait_for_edge(self.pin, GPIO.BOTH,timeout=timeout)

			if f is None: continue
			if f != self.pin: continue
			if self.verb: print("lbo: pin {} has crossed edge".format(self.pin))

			sleep(1)
			if self.goodbat():
				if state == "pending":
					sleep(1)
					if self.goodbat():
						if self.verb: print("lbo: power restored within grace time expired, cancelling lbo action")
						self.cancelcb()
						state = "running"
				continue

			if state == "running":
				start = time()
				if self.verb: print("lbo: low battery alert, commencing grace period ({} seconds)".format(self.grace))
				self.gracecb()
				state = "pending"

	def stop(self):
		self.keeprunning=False

def poweroff():
	m="shutting down due to low battery signal"
	print(m)
	call(["wall",m])
	sleep(1)
	call(["sudo","poweroff"])

if __name__ == "__main__":
	import os,sys
	from signal import pause

	def fakepoweroff():
		m="low battery signal received"
		print(m)

	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

	if (len(sys.argv) > 1):
		pin = int(sys.argv[1])
	else:
		pin = 26

	try:
		lb=lbo(pin,grace=10,callback=fakepoweroff)
		lb.start()
		pause()
	except:
		print("exiting")
		lb.stop()
		exit(0)
