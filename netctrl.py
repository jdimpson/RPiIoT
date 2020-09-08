#!/usr/bin/python
from subprocess import check_output,STDOUT

####
# IP level settings
####
def ifdown(iface="wlan0"):
	return _ifud("/sbin/ifdown", iface=iface)

def ifup(iface="wlan0"):
	return _ifud("/sbin/ifup", iface=iface)

def _ifud(proc,iface="wlan0"):
	o = check_output([proc, iface], stderr=STDOUT)
	if len(o) == 0: o = "OK"
	return o

####
# Wireless interface settings using iw, iwlist, or iwconfig
####

# region BO reported has no TX limits (goes up to 30 by spec)
def wifisetregion(reg="US",iface="wlan0"):
	o = check_output(["/sbin/iw","reg","set",reg],stderr=STDOUT)
	if len(o) == 0: o = "OK"
	return o

def wifitxpower(iface="wlan0",power=27):
	if power > 27:
		print "Warning: {p} is higher than US region limitation (you sly dog)".format(p=power)
	o = check_output(["/sbin/iwconfig",iface,"txpower",power],stderr=STDOUT)
	if len(o) == 0: o = "OK"
	return o

####
# Wireless network settings using wpa_supplicant (via wpa_cli)
####

def wpa_reassociate(iface="wlan0"):
	return _wpa_checkresults(_wpacli("reassociate",iface=iface))

def wpa_addssid(ssid,psk=None,enable=True,iface="wlan0"):
	# NOTE: this doesn't prevent you from addin the same SSID more than once.
	o = _wpacli("add_network",iface=iface)
	netwnum = o.rstrip() # this needs to be a string
	qssid = '"{ssid}"'.format(ssid=ssid)
	o = _wpacli(["set_network",netwnum,"ssid",qssid],iface=iface)
	o = _wpa_checkresults(o)
	if o is False: return None
	if psk is not None:
		qpsk = '"{psk}"'.format(psk=psk)
		o = _wpacli(["set_network",netwnum,"psk",qpsk],iface=iface)
		o = _wpa_checkresults(o)
		if o is False: return None
	if enable:
		o = _wpacli(["enable_network",netwnum],iface=iface)
	else:
		o = _wpacli(["disable_network",netwnum],iface=iface)
	o = _wpa_checkresults(o)
	if o is False: return None
	return int(netwnum)

def wpa_removessid(ssid,iface="wlan0"):
	r = True
	if isinstance(ssid,str):
		ssid = wpa_findssid(ssid)
	elif not isinstance(ssid,list):
		ssid = [ ssid ]
	for s in ssid:
		netnum = s["network"]
		o = _wpacli(["remove_network",str(netnum)],iface=iface)
		o = _wpa_checkresults(o)
		r = r & o
	return r

def wpa_findssid(ssid,iface="wlan0"):
	o = []
	for net in wpa_configurednetworks(iface=iface):
		if net["ssid"] == ssid:
			o.append(net)
	return o

def wpa_configurednetworks(iface="wlan0"):
	#network id / ssid / bssid / flags
	#0	bounty	any
	#1	Edimax	any
	#2	aptsec	any
	#3	SPRJ-1	any
	#4	SPRJ-2	any	[DISABLED]
	#5	any
	o = _wpacli("list_networks",iface=iface)
	for line in o.splitlines():
		if "network id" in line:
			continue
		
		num   = int(line[:line.find('\t')].rstrip())
		line  = line[line.find('\t')+1:]
		ssid  = line[:line.find('\t')].rstrip()
		line  = line[line.find('\t')+1:]
		bssid = line[:line.find('\t')].rstrip()
		line  = line[line.find('\t')+1:]
		flags = line
		yield({
			"network":num,
			   "ssid":ssid,
			  "bssid":bssid,
			  "flags":flags,
		})

def _wpacli(args,iface="wlan0"):
	cmd = ["/sbin/wpa_cli","-i",iface]
	if not isinstance(args,list):
		args = [ args ]
	return check_output(cmd + args, stderr=STDOUT)

def _wpa_checkresults(o):
	o = o.rstrip()
	if o == "FAIL":
		return False
	if o != "OK":
		print "Unknown return value {}, assuming failure".format(o)
		return False
	return True

if __name__ == "__main__":
	import sys,os
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

	wpa_addssid("nonlmuser",psk="nonlmuser",enable=True)
	for x in wpa_findssid("SGNBLACK"): print x["network"]
	wpa_removessid("SGNBLACK")
	for x in wpa_findssid("SGNBLACK"): print x["network"]
	exit()

	def usage():
		return '''
usage: {me} <command> [interface]
where command is
	help
	associate or reassociate or just assoc
	up
	down
	updown
'''

        cmd = "assoc"
	iface = "wlan0"
	if len(sys.argv) > 1:
		cmd = sys.argv[1]
	if len(sys.argv) > 2:
		iface = sys.argv[2]

	if cmd == "help":
		print usage()
	elif "assoc" in cmd:
		print "Reassociating ssid of {iface}:".format(iface=iface),
		print wpa_reassociate(iface)
	elif cmd == "down":
		print "Taking {iface} down:".format(iface=iface),
		print ifdown(iface)
	elif cmd == "up":
		print "Bringing {iface} up:".format(iface=iface),
		print ifup(iface)
	elif cmd == "updown":
		print "Taking {iface} down:".format(iface=iface),
		print ifdown(iface)
		print "Bringing {iface} up:".format(iface=iface),
		print ifup(iface)

