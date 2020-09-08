#!/usr/bin/python
from subprocess import check_output,CalledProcessError
from platform   import node
from socket     import gethostname
from time	import time,strftime,localtime

wifiscan_fields = ["ssid", "address", "date", "quality", "signaldBm", "channel", "frequencyGHz", "wpa_ver", "pairwise_ciphers", "auth_suites", "timestamp", "rateMbps", "encryption", "mode", "extras", "ie_unknown", "group_cipher"]

def _pl(pattern, line,end=None):
	if end is None:
		o = line[line.find(pattern) + len(pattern):]
	else:
		o = line[line.find(pattern) + len(pattern): line.find(end)]
	return o.lstrip().rstrip()

def wifiscan_text(iface="wlan0"):
	o = ''
	for e in wifiscan(iface=iface):
		o += wifiscan_format(e)
	return o

def wifiscan_format(e):
	e["date"] = strftime("%Y-%m-%d %H:%M:%S %Z",localtime(e["timestamp"]))
	return '''\
{ssid}	{address}
	{date}
	{quality}
	{signaldBm} dBm
	channel {channel}
	{frequencyGHz} GHz
	{wpa_ver} {pairwise_ciphers} {auth_suites}
'''.format(**e)

def wifiscan_collate(iface="wlan0", addresses = {}, ssids = {}, timestamps = {}):
	for e in wifiscan(iface=iface):
		if not e["ssid"] in ssids:
			ssids[e["ssid"]] = []
		ssids[e["ssid"]].append(e)
		if not e["address"] in addresses:
			addresses[e["address"]] = []
		addresses[e["address"]].append(e)
		if not e["timestamp"] in timestamps:
			timestamps[e["timestamp"]] = []
		timestamps[e["timestamp"]].append(e)
	return addresses,ssids,timestamps

def wifiscan_instantiate(instance=None):
	if instance is None:
		instance = {}
	for f in wifiscan_fields:
		if f not in instance:
			instance[f] = None
	return instance

def wifiscan(iface="wlan0"):
	# inspired by http://faradaysclub.com/?p=1016
	stamp = int(time())
	scanoutput = check_output(["/sbin/iwlist", iface, "scan"])
	e = {}
	for l in scanoutput.splitlines():
		if "Cell" in l and len(e): # next record
			e["timestamp"] = stamp
			if "ratesMbs" in e:
				t = e["ratesMbs"] + "; "
 				t = t.split(" Mb/s; ")[:-1]
				t = [float(x) for x in t]
				e["ratesMbs"] = t
			if "wpa_ver" not in e:
				e["wpa_ver"]={ "WPA": -1}
			e=wifiscan_instantiate(e)
			yield(e)
			e={}

		if "No scan results" in l:
			# try again later, or as root
			return

		if l == "" or "Scan completed" in l:
			pass
		elif "Cell" in l and "Address: " in l:
			# Cell 01 - Address: 68:C4:4D:A8:F9:1A
			e["address"] = _pl("Address: ",l)
		elif "Channel:" in l:
			# Channel:9
			e["channel"] = int(_pl("Channel:",l))
		elif "Frequency:" in l:
			# Frequency:2.452 GHz (Channel 9)
			t = _pl("Frequency:",l, end=" GHz ")
			e["frequencyGHz"] =float(t)
		elif "Quality=" in l:
			# Quality=70/70  Signal level=-37 dBm
			e["quality"] = _pl("Quality=",l, end="Signal ")
			e["signaldBm"] = int(_pl("Signal level=",l, end=" dBm"))
		elif "Encryption key:" in l:
			# Encryption key:on
			t = _pl("Encryption key:",l)
			if t == "on":
				e["encryption"] = True
			elif t == "off":
				e["encryption"] = False
			else:
				raise RuntimeError("Unknown encryption key value {t}".format(t=t))
		elif "ESSID:" in l:
			# ESSID:"bounty"
			e["ssid"] = _pl('ESSID:',l)
			e["ssid"] = e["ssid"][1:-1]
		elif "Bit Rates:" in l:
			# Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s
			# Bit Rates:6 Mb/s; 9 Mb/s; 12 Mb/s; 18 Mb/s; 24 Mb/s
			#           36 Mb/s; 48 Mb/s; 54 Mb/s
			if "ratesMbs" in e:
				# second line
				e["ratesMbs"] = e["ratesMbs"]+ "; " + _pl("Bit Rates:",l)
			else:
				# first line
				e["ratesMbs"] = _pl("Bit Rates:",l)
		elif "Mb/s" in l:
			# third line of ratesMbs
			e["ratesMbs"] = e["ratesMbs"]+ "; " + _pl("                              ",l)	
		elif "Mode:" in l:
			# Mode:Master
			e["mode"] = _pl("Mode:",l)
		elif "Extra:" in l:
			# Extra:tsf=0000000000000000
			# Extra: Last beacon: 12090ms ago
			t = _pl("Extra:",l)
			if not "extras" in e:
				e["extras"] = []
			e["extras"].append(t)
		elif "IE: Unknown: " in l:
			# IE: Unknown: 0006626F756E7479
			# IE: Unknown: 010482848B96
			# IE: Unknown: 030109
			# IE: Unknown: 0509000200000000000000
			t = _pl("IE: Unknown:",l)
			if not "ie_unknown" in e:
				e["ie_unknown"] = []
			e["ie_unknown"].append(t)
		elif "IE: WPA Version " in l:
			t = _pl("IE: WPA Version ",l)
			e["wpa_ver"]={ "WPA": int(t)}
		elif "IE: IEEE 802.11i/WPA2 Version " in l:
			# IE: IEEE 802.11i/WPA2 Version 1
			t = _pl("IE: IEEE 802.11i/WPA2 Version ",l)
			e["wpa_ver"]={"WPA2":int(t)}
		elif "Group Cipher : " in l:
			# Group Cipher : CCMP
			e["group_cipher"] = _pl("Group Cipher : ",l)
		elif "Pairwise Ciphers" in l:
			# Pairwise Ciphers (1) : CCMP
			t = _pl(" : ",l)
			e["pairwise_ciphers"] = t
		elif "Authentication Suites" in l:
			# Authentication Suites (1) : PSK
			t = _pl(" : ",l)
			e["auth_suites"] = t
		else:
			raise RuntimeError('''Unrecognized iwlist output line "{l}"'''.format(l=l))

def net(iface="wlan0"):
	mac=ipv4=ipv6=None
	try:
		ip = check_output(["/bin/ip","addr", "show", "dev", iface])
	except CalledProcessError as e:
		return mac,ipv4,ipv6
	for line in ip.splitlines():
		if "link/ether" in line:
			mac = line.split()[1]
		elif "inet6" in line:
			ipv6 = line.split()[1]
		elif "inet" in line:
			ipv4 = line.split()[1]
	return mac,ipv4,ipv6

def iwconfig_text(iface="wlan0"):
	e = iwconfig(iface)
	return iwconfig_format(e)

def iwconfig_format(e):
	return '''\
{iface}	IEEE 802.11 ESSID:"{ssid}"
	Mode:{mode} Frequency:{frequency} Access Point:{access point}
	Bit Rate={bit rate} Tx-Power={txpower}
	Retry short limit:{retry short limit} RTS thr:{rts thr} Fragment thr:{fragment thr}
	Power Management:{power management}
	Link Quality={link quality} Signal level={signal level}
	Rx invalid nwid:{rx invalid nwid} Rx invalid crypt:{rx invalid crypt} Rx invalid frag:{rx invalid frag}
	Tx excessive retries:{tx excessive retries} Invalid misc:{invalid misc} Missed beacon:{missed beacon}
'''.format(**e)

def iwconfig(iface="wlan0"):
	e = {"iface":iface}
	try:
		iw = check_output(["/sbin/iwconfig",iface])
	except CalledProcessError as e:
		return ssid,qual,chan
	for line in iw.splitlines():
		# wlan0     IEEE 802.11  ESSID:"aptsec"
		if "ESSID" in line:
			t = _pl("ESSID:",line)
			if '"' in t: # quote means SSID
				ssid = t[1:-1]
			elif "off" in t:
				ssid = None
			e["ssid"] = ssid

		# Mode:Managed  Frequency:2.447 GHz  Access Point: DC:A5:F4:DE:DE:E0
		if "Mode:" in line:
			t = _pl("Mode:",line,end="Frequency")
			e["mode"] = t
		if "Frequency:" in line:
			t = _pl("Frequency:",line,end="Access Point")
			e["frequency"] = t
		if "Access Point" in line:
			t = _pl("Access Point:",line)
			e["access point"] = t

		# Bit Rate=72.2 Mb/s   Tx-Power=31 dBm 
		if "Bit Rate=" in line:
			t = _pl("Bit Rate=",line,end="Tx-Power")
			e["bit rate"] = t
		if "Tx-Power=" in line:
			t = _pl("Tx-Power=",line)
			e["txpower"] = t
		# Bit Rate:72.2 Mb/s   Sensitivity:0/0
		if "Bit Rate:" in line:
			t = _pl("Bit Rate:",line,end="Sensitivity")
			e["bit rate"] = t
			e["txpower"] = None
 

		# Retry short limit:7   RTS thr:off   Fragment thr:off
		if "Retry short limit:" in line:
			t = _pl("Retry short limit:", line, end="RTS thr")
			e["retry short limit"] = int(t)
		# Retry:off   RTS thr:off   Fragment thr:off
		if "Retry:" in line:
			t = _pl("Retry:", line, end="RTS thr")
			if t == "off": t = -1
			e["retry short limit"] = int(t)
		if "RTS thr:" in line:
			t = _pl("RTS thr:",line,end="Fragment thr")
			try:    t = int(t)
			except: pass
			e["rts thr"] = t
		if "Fragment thr:" in line:
			t = _pl("Fragment thr:",line)
			try:    t = int(t)
			except: pass
			e["fragment thr"] = t
			
		# Power Management:on
		if "Power Management:" in line:
			t = _pl("Power Management:",line)
			e["power management"] = t

		# Link Quality=65/70  Signal level=-45 dBm 
		if "Link Quality=" in line:
			t = _pl("Link Quality=",line,end="Signal level")
			e["link quality"] = t
		if "Signal level=" in line:
			t = _pl("Signal level=",line)
			e["signal level"] = t

		# Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
		if "Rx invalid nwid:" in line:
			t = _pl("Rx invalid nwid:",line,end="Rx invalid crypt")
			e["rx invalid nwid"] = int(t)
		if "Rx invalid crypt:" in line:
			t = _pl("Rx invalid crypt:",line,end="Rx invalid frag")
			e["rx invalid crypt"] = int(t)
		if "Rx invalid frag:" in line:
			t = _pl("Rx invalid frag:",line)
			e["rx invalid frag"] = int(t)

		# Tx excessive retries:6  Invalid misc:0   Missed beacon:0
		if "Tx excessive retries:" in line:
			t = _pl("Tx excessive retries:",line,end="Invalid misc")
			e["tx excessive retries"] = int(t)
		if "Invalid misc:" in line:
			t = _pl("Invalid misc:",line,end="Missed beacon")
			e["invalid misc"] = int(t)
		if "Missed beacon:" in line:
			t = _pl("Missed beacon:",line)
			e["missed beacon"] = int(t)
	return e

def iwc(iface="wlan0"):
	ssid = None
	qual = None
	chan = None
	t = iwconfig(iface=iface)
	ssid = t["ssid"]
	qual = t["signal level"]
	if " dBm" in qual:
		qual = qual[:qual.find(" dBm")]
	try:
		iw = check_output(["/sbin/iw","dev",iface,"info"])
	except CalledProcessError as e:
		return ssid,qual,chan
	for line in iw.splitlines():
		if "channel" in line:
			word = line.split()[1]
			chan = word
	if qual is not None:
		qual = int(qual)
	if chan is not None:
		chan = int(chan)
	return ssid,qual,chan

def wpainfo(iface="wlan0"):
	bssid=freq=ssid=wpa_state=ip_address=mac_address=None
	cmd = "status"
	try:
		wpa = check_output(["/sbin/wpa_cli", "-i" ,iface, cmd])
	except CalledProcessError as e:
		return {
			"bssid": bssid,
			"freq": freq,
			"ssid": ssid,
			"wpa_state": wpa_state,
			"ip_address": ip_address,
			"mac_address": mac_address,
		}
	for line in wpa.splitlines():
		if "bssid=" in line:
			bssid=line[line.find("=")+1:]
		elif "freq=" in line:
			freq=line[line.find("=")+1:]
		elif "ssid=" in line:
			ssid=line[line.find("=")+1:]
		elif "wpa_state=" in line:
			wpa_state=line[line.find("=")+1:]
		elif "ip_address=" in line:
			ip_address=line[line.find("=")+1:]
		elif "address=" in line:
			mac_address=line[line.find("=")+1:]
	return {
		"iface": iface,
		"bssid": bssid,
		"freq": freq,
		"ssid": ssid,
		"wpa_state": wpa_state,
		"ip_address": ip_address,
		"mac_address": mac_address,
	}
### wpa state machine per https://netbeez.net/blog/linux-wireless-engineers-read-wpa-supplicant-logs/
#       SCANNING -> ASSOCIATING
#    ASSOCIATING -> ASSOCIATED
#     ASSOCIATED -> 4WAY_HANDSHAKE
# 4WAY_HANDSHAKE -> 4WAY_HANDSHAKE   # some internal quirk i guess
# 4WAY_HANDSHAKE -> GROUP_HANDSHAKE
#GROUP_HANDSHAKE -> COMPLETED


def wpainfo_text(iface="wlan0"):
	wp = wpainfo(iface)
	wp["iface"] = iface
	return '''
 ssid: {ssid}	iface: {iface}
 freq: {freq}
state: {wpa_state}
   ip: {ip_address}
  mac: {mac_address}
bssid: {bssid}
'''.format(**wp)
	

def netinfo(iface="wlan0"):
	nod = node()
	host = gethostname()
	ssid,qual,chan = iwc(iface)
	mac,ipv4,ipv6 = net(iface)
	if qual is None: qual = 0
	if chan is None: chan = 0
	return {
		'iface': iface,
		 'node': nod,
		 'host': host,
		 'ssid': ssid,
		 'qual': qual,
		 'chan': chan,
		  'mac': mac,
		 'ipv4': ipv4,
		 'ipv6': ipv6,
	}

def netinfo_text(iface="wlan0"):
	ni = netinfo(iface)
	return '''
 node: {node}\thost: {host}
iface: {iface}\tssid: {ssid}
 chan: {chan}\tqual: {qual}
  mac: {mac}
 ipv4: {ipv4}
 ipv6: {ipv6}
'''.format(**ni)

def netwait(iface="wlan0"):
	wi = wpainfo(iface)
	while wi['wpa_state'] != 'COMPLETED':
		sleep(10)
		wi = wpainfo(iface)


if __name__ == "__main__":
	from time import sleep
	from sys import argv
	
	try:
		arg1 = argv[1]
	except:
		arg1 = None

	iface = "wlan0"
	if arg1 is not None:
		if arg1 == "wait":
			print "Waiting for net"
			netwait()
		else:
			iface = arg1

	print(iwconfig_text())
	exit(0)

	print netinfo_text()
	print wpainfo_text()
	print wifiscan_text()
	exit()

	print "first scan"
	addresses, ssids, timestamps = wifiscan_collate()
	print "sleep 30"
	sleep(30)
	print "second scan"
	addresses, ssids, timestamps = wifiscan_collate(addresses=addresses,ssids=ssids, timestamps=timestamps)
	for a in ssids:
		for e in ssids[a]:
			print wifiscan_format(e)
