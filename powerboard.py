#!/usr/bin/env python
from gpiozero	import PWMLED 
from signal	import pause
from time	import sleep
from subprocess	import call, Popen
from threading	import Thread
from os		import access, X_OK

from multibutton import multibutton
from lbo         import lbo
from netinfo     import netinfo,wpainfo
from netctrl     import ifup,ifdown,wpa_reassociate
from wall        import alert,popup
from kvgetopts   import kvgetopts

###
# When running from boot, pulse until wifi gets link
#                      then off after wifi gets link
# XWhen button is short pressed, toggle solid LED on/off
# XWhen button is long pressed (>=5 sec), flash until by poweroff
# XWhen low battery is asserted, flash for 60 secs, continue flash until poweroff
# Poweroff overrules low battery overrules short button overrules wifi state
###
class powerboard(object):
	iface="wlan0"
	grace=60
	led=None
	button=None
	lowpower=None

	def poweroff(self,s=1,m="Shutting down",usesudo=True):
		alert(m)
		sleep(s)
		if usesudo:
			call(["sudo","poweroff"])
		else:
			call(["poweroff"])

	def wifiassoc(self):
		if self.led: self.led.blink(on_time=0.1,off_time=0.1)
		m="Reassociating ssid of {iface}".format(iface=self.iface)
		popup(m=m)
		alert(m=m)
		wpa_reassociate(self.iface)
		while True:
			sleep(1)
			w = wpainfo()
			if w["wpa_state"] == "COMPLETED":
				if w['ip_address'] is not None:
					m="IPv4 address is {ip_address}".format(**w)
					popup(m=m)
					alert(m=m)
					if self.led: self.led.off()
					return

		#m="Taking {iface} down".format(iface=iface)
		#popup(m=m)
		#alert(m=m)
		#ifdown(iface)
		#m="Bringing {iface} up".format(iface=iface)
		#popup(m=m)
		#alert(m=m)
		#ifup(iface)
		#while True:
		#	n = netinfo()
		#	if n["ipv4"] is not None:
		#		m="IPv4 address is {ipv4}".format(**n)
		#		popup(m=m)
		#		alert(m=m)
		#		led.off()
		#		return

	def ledshutdown(self):
		self.ledblink(on=0.1,off=0.1)
		self.poweroff(s=3, m="Shutting down in 3 seconds due to long button press")

	def popupshutdown(self):
		m="Shutting down in 3 seconds due to long button press"
		popup(m=m)
		self.poweroff(s=3, m=m)

	def ledblink(self,on=0.05,off=0.1):
		if self.led: 
			self.led.off()
			self.led.blink(on_time=on,off_time=off)

	def cancelled(self):
		if self.led:
			self.led.off()
		alert("Shutdown cancelled")

	def ledlowbatterywarn(self):
		self.ledblink()
		alert("Shutting down in {} seconds due to to Low Battery signal".format(60))

	def lowbatteryshut(self):
		self.poweroff(s=3, m="Shutting down in 3 seconds")

	def popuplowbattery(self):
		m="Shutting down in 1 minute due to Low Battery signal"
		popup(m=m)
		self.poweroff(s=3, m=m)

	def popupbutton(self):
		popup(m="Button was pressed!")

	def toggleled(self):
		m="toggling led"
		alert(m)
		if self.led:
			if self.led.is_lit:
				self.led.off()
			else:
				self.led.on()

	def mypopen(self,s):
		print("running {}".format(s))
		return Popen([s])

	def findcb(self,s):
		if access(s, X_OK):
			return lambda: self.mypopen(s)
		
		if s == "toggleled":       return self.toggleled
		if s == "popupbutton":     return self.popupbutton
		if s == "alert":           return alert
		if s == "ledshutdown":     return self.ledshutdown 
		if s == "popupshutdown":   return self.popupshutdown
		if s == "wifiassoc":       return self.wifiassoc 
		if s == "ledblink":        return self.ledblink
		if s == "ledlowbatterywarn":   return self.ledlowbatterywarn
		if s == "popuplowbattery": return self.popuplowbattery
		print("Warning: callback {} not found!".format(s))
		return lambda: None

if __name__ == "__main__":
        from sys import argv
	import sys,os
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
	ledpin = None
	butpin = None
	lbopin = None
	testled = False
	ackpress = False
	active_high = True

	pb = powerboard()

       	shortcb       = pb.findcb("toggleled")
	mediumcb      = pb.findcb("alert")
	longcb        = pb.findcb("ledshutdown")
	doublecb      = pb.findcb("wifiassoc")
	triplecb      = None
	long_flash_cb = pb.findcb("ledblink")

	if len(argv) > 1:
		opts = kvgetopts(argv)
		ledpin = opts.get('led',ledpin)
		butpin = opts.get('but',butpin)
		lbopin = opts.get('lbo',lbopin)
		pb.grace = opts.get('grace',None)
		tmp = opts.get('long',None)
		if tmp is not None: longcb = pb.findcb(tmp)
		tmp = opts.get('triple',None)
		if tmp is not None: triplecb = pb.findcb(tmp)
		tmp = opts.get('double',None)
		if tmp is not None: doublecb = pb.findcb(tmp)
		tmp = opts.get('medium',None)
		if tmp is not None: mediumcb = pb.findcb(tmp)
		tmp = opts.get('short',None)
		if tmp is not None: shortcb = pb.findcb(tmp)

		for a in opts.remains[1:]:	# skip name of executable
			if a.startswith("active"):
				if "low" in a:
					active_high = False
				elif "high" in a:
					active_high = True
				else:
					raise RuntimeError("Unrecognized argument {}".format(a))
			elif a.startswith("testled"):
				testled=True
			elif a.startswith("ackpress"):
				ackpress=True
			else:
				raise RuntimeError("Unrecognized argument {}".format(a))


	if ledpin is None and butpin is None and lbopin is None:
		# These happen to be the pins as used by powerboard v2.0
		ledpin = 27
		butpin = 17
		lbopin = 26

	print "led={l} but={b} lbo={o}".format(l=ledpin,b=butpin,o=lbopin)


	if ledpin: 
		pb.led  = PWMLED(ledpin, active_high=active_high) 
	else:
		pb.led = None

	if ackpress:
		if pb.led is not None:
			def tmp():
				pb.led.on()
				sleep(0.25)
				pb.led.off()
				sleep(0.1)
			ackpress = tmp
		else:
			raise RuntimeError("ackpress flag given, but no LED defined")
	else:
		ackpress = None

	if butpin:
		print(ackpress)
		pb.button = multibutton(butpin, pull_up=True, shortcb=shortcb, mediumcb=mediumcb, longcb=longcb, doublecb=doublecb, triplecb=triplecb, long_flash_cb=long_flash_cb, ackpress=ackpress)
	else:
		pb.button = None

	if lbopin:
		try:
			pb.lowpower = lbo(lbopin,grace=pb.grace,callback=pb.lowbatteryshut,gracecb=pb.ledlowbatterywarn,cancelcb=pb.cancelled)
			pb.lowpower.start()
		except RuntimeError as e:
			print e

	if pb.led and testled:
		pb.led.pulse()
		sleep(3)
		pb.led.off()

	#print "Waiting for WiFi"
	#c=0
	#while True:
	#	w=wpainfo(iface)
	#	if w["wpa_state"] == "COMPLETED":
	#		print "WiFi found"
	#		break
	#	c+=1
	#	if c >= 300:
	#		print "Giving up on WiFi "
	#		continue
		
	try:
		pause()
	except:
		if pb.lowpower is not None:
			pb.lowpower.stop()

	exit(1)
