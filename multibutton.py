#!/usr/bin/env python
import sys
from gpiozero	import Button
from datetime	import datetime,timedelta
from time	import sleep
from subprocess	import call
from threading	import Timer
from inspect	import getargspec,ismethod,isfunction

class multibutton(object):
	#verb = True
	verb = False
	PULLDOWN_WORKAROUND=False
	def __init__(self,pin,pull_up=True,shortcb=None,mediumcb=None,longcb=None,doublecb=None,triplecb=None,long_flash_cb=None,ackpress=None):
		self.pin      = pin
		self.pull_up  = pull_up
		self.button_down_time=datetime(1970, 1, 1, 1, 1, 1)
		self.button_up_time=datetime(1970, 1, 1, 1, 1, 10)
		self.button = Button(self.pin, pull_up=pull_up)
		self.button.when_pressed  = self.pressed_button_handler
		self.button.when_released = self.released_button_handler
		if self.PULLDOWN_WORKAROUND and pull_up == False:
			if self.verb: print("Using PULLDOWN_WORKAROUND")
			self.button.when_pressed  = self.released_button_handler
			self.button.when_released = self.pressed_button_handler
		self.long_flash_timer = None
		self.ackpress = ackpress
		if self.verb: print("{t} waiting pulled {dir} on pin {p} for button events".format(p=self.pin,dir="up" if pull_up else "down", t=datetime.now()))

		# used to distinguish buttons
		self.pressed_count=0
		self.last_down_time=datetime(1970, 1, 1, 1, 1, 1)
		self.double_press_limit=0.5
		self.press_lengths = {
			'short':0.5,
			'medium':3,
			'long':"default",
		}

		# Timer to distinguish short press from double press
		self.delayedsingle = None
		self.delayeddouble = None

		# callbacks for button presses
		self.setshortcb(shortcb)
		self.setmediumcb(mediumcb)
		self.setlongcb(longcb)
		self.setdoublecb(doublecb)
		self.settriplecb(triplecb)
		self.setlongflashcb(long_flash_cb)

	def setshortcb(self,shortcb):
		self.shortcb  = shortcb
	def setmediumcb(self,mediumcb):
		self.mediumcb = mediumcb
	def setlongcb(self,longcb):
		self.longcb   = longcb
	def setlongflashcb(self,longflashcb):
		self.long_flash_cb   = longflashcb
	def setdoublecb(self,doublecb):
		self.doublecb = doublecb
	def settriplecb(self,triplecb):
		self.triplecb = triplecb

	def close(self): 
		sys.stderr.write("WARNING: close() in multibutton calls close() in gpiozero which calls close() in RPi.GPIO, which in 0.6.3 is buggy (https://sourceforge.net/p/raspberry-gpio-python/tickets/145/) and ultimately closes all your current buttons. You either need to change your pin factory (https://gpiozero.readthedocs.io/en/stable/api_pins.html#changing-the-pin-factory) or change your algorithm to avoid needing to close buttons (e.g. change your callbacks instead).\n")
		return self.button.close()

	def pressed_button_handler(self):
		if self.long_flash_cb is not None:
			self.long_flash_timer=Timer(self.press_lengths['medium'], lambda: self.callcallback(self.long_flash_cb,self.pin,event="long_flash"))
			self.long_flash_timer.start()
		if self.verb: print "button on pin {p} depressed".format(p=self.pin)
		self.last_down_time   = self.button_down_time
		self.button_down_time = datetime.now()
	
	def released_button_handler(self):
		self.button_up_time = datetime.now()
		if self.verb: print "button on pin {p}  released".format(p=self.pin)
		if self.long_flash_timer is not None:
			self.long_flash_timer.cancel()
			self.long_flash_timer=None

		button_pressed_delta = self.button_up_time - self.button_down_time

		ev=None
		cb=None
		if button_pressed_delta < timedelta(seconds=self.press_lengths['short']):
			if self.doublecb is None and self.triplecb is None:
				ev = 'short'
				cb = self.shortcb
			else:
				if self.delayeddouble is not None:
					self.delayeddouble.cancel()
					self.delayeddouble = None
					ev = 'triple'
					if self.triplecb is None:
						ev = 'double'
						cb = self.doublecb
					else:
						ev = 'triple'
						cb = self.triplecb
				elif self.delayedsingle is not None:
					self.delayedsingle.cancel()
					self.delayedsingle = None
					ev = 'double'
					def tmp():
						if self.verb: print "Executing {v} for {e}, at {d}".format(v=self.doublecb,e=ev,d=button_pressed_delta)
						if self.doublecb is not None:
							self.callcallback(self.doublecb,self.pin,ev)
						self.delayeddouble = None

					self.delayeddouble=Timer(self.double_press_limit, tmp)
 					self.delayeddouble.start()
					return
				else:
					ev="short"
					def tmp():
						if self.verb: print "Executing {v} for {e}, at {d}".format(v=self.shortcb,e=ev,d=button_pressed_delta)
						if self.shortcb is not None:
							#self.shortcb()
							self.callcallback(self.shortcb,self.pin,ev)
						self.delayedsingle = None

					self.delayedsingle=Timer(self.double_press_limit, tmp)
 					self.delayedsingle.start()
					return
		elif button_pressed_delta < timedelta(seconds=self.press_lengths['medium']): 
			ev = 'medium'
			cb = self.mediumcb
		else:
			ev = 'long'
			cb = self.longcb
		if self.verb: print "Executing {v} for {e}, at {d}".format(v=cb,e=ev,d=button_pressed_delta)
		self.callcallback(cb,self.pin,ev)

	def callcallback(self,cb,buttonpin,event="unknown"):
		if self.verb : print("Entered callcallback")
		if cb is None:
			if self.verb : print("Callback is None")
			return None
		if self.ackpress is not None:
			self.ackpress()
		args,varargs,keywords,defaults=getargspec(cb)
		l=len(args)
		if ismethod(cb):
			l-=1 # ignore "self"
			# this may not be wise. probably better to look for specifically named arguments in the args array
		if l == 1:
			return cb(buttonpin)
		elif l == 2:
			return cb(buttonpin,event)
		else:
			return cb()

	def __repr__(self):
		return "<{cls} pin {p}>".format(cls=self.__class__.__name__, p=self.pin)

def alert(m="Alert! There is no alert."):
	print(m)
	call(["wall",m])

def poweroff(sec=3):
	m="Shutting down in {s} seconds due to button press".format(s=sec)
	alert(m)
	sleep(sec)
	call(["sudo","poweroff"])

pressed_count = {}
def increment(button,event):
	global pressed_count
	if not button in pressed_count:
		pressed_count[button] = {}
	if not event in pressed_count[button]:
		pressed_count[button][event] = 0

	pressed_count[button][event]+=1
	#import threading
	#m="button on pin {b} {e}-pressed {t} times (thread {x})".format(b=button,e=event,t=pressed_count[button][event],x=threading.current_thread())
	m="button on pin {b} {e}-pressed {t} times".format(b=button,e=event,t=pressed_count[button][event])
	alert(m)

if __name__ == "__main__":
	from signal import pause
	from sys    import argv

	from kvgetopts import kvgetopts

	kv = kvgetopts(argv)
	argv = kv.remains

	pull_up = bool(kv.get("pull_up", True))
	if not pull_up:
		multibutton.verb = True
		multibutton.PULLDOWN_WORKAROUND = True

	if len(argv) > 1:
		o = []
		for p in argv[1:]:
			p = int(p)
			print "pin {}".format(p)
			o.append(multibutton(p, pull_up=pull_up, shortcb=increment,mediumcb=increment,longcb=increment,doublecb=increment,triplecb=increment,long_flash_cb=lambda p: alert("Long hold alert for pin {}".format(p))))
	else:
		p=19
		print "pin {}".format(p)
		o=[multibutton(p, pull_up=pull_up, shortcb=increment,mediumcb=increment,longcb=increment,doublecb=increment,triplecb=increment,long_flash_cb=lambda p: alert("Long hold alert for pin {}".format(p)))]
	print "ready to test: " + str(o)
	pause()
