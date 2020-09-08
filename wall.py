#!/usr/bin/env python

from subprocess import check_call, CalledProcessError, Popen
from shlex      import split
from os         import environ

defmesg = "Alert! (There is no alert.)"
zenity = "/usr/bin/zenity"

# from https://www.dropbox.com/s/8mkc4m6617xh7hm/test.py?dl=0
def redalert(m="RED ALERT"):
	ansi = "echo -ne '\e[s''\e[1;56H''\e[1;31m'{m}'\e[u''\e[0m'".format(m=m)
	try:
		check_call(split(ansi))
	except OSError as e:
		print("Can't redalert: {}".format(e))
	except CalledProcessError as e:
		print("Can't redalert: {}".format(e))

def popup(m=defmesg):
	print("Can't popup; not in windowing environment")

if "DISPLAY" in environ and environ["DISPLAY"] != "":
	er=None
	try:
		check_call([zenity])
	except CalledProcessError as e:
		er = e
	except OSError as e:
		er=None

	if er is not None and er.returncode == 255:
		def popup(m=defmesg):
			print(m)
			Popen([zenity, "--info", "--text={}".format(m)])

def alert(m=defmesg):
	print(m)
	try:
		check_call(["wall",m])
	except OSError as e:
		print("Can't wall: {}".format(e))
	except CalledProcessError as e:
		print("Can't wall: {}".format(e))

if __name__ == "__main__":
	redalert()
	print("alert test, default message")
	alert()
	print("popup test, default message")
	popup()
	print("alert test, custom message")
	alert(m="this is a custom message")
	print("popup test, custom message")
	popup(m="this is a custom message")
