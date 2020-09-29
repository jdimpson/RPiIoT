#!/usr/bin/python

import subprocess
import atexit

# in this instance I like a generator better than a class
def udisk(debug=False):
	proc=None

	if debug: print("udisk(): Monitoring for new mounts")
	def udiskpipe():
		cmd = ["udisksctl", "monitor"]
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		def udiskstop():
			if proc is None:
				return
			if debug: print "udisk(): Cleaning up udiskctl"
			try:
				proc.terminate()
				proc.kill()
			except OSError:
				pass
			proc.wait()
			return 
		atexit.register(udiskstop)
		return proc.stdout

	def find_disk(line):
		lizt = line.split(":")
		key=lizt[0].strip()
		if len(lizt) > 1:
			val=lizt[1].strip()
			if val == '':
				val = None
		else:
			val = None
		if key == "MountPoints" and val is not None:
			if debug: print "udisk(): {k} = '{v}'".format(k=key, v=val)
			return val

	pipe = udiskpipe()
	while True:
		line = pipe.readline().strip()
		mp = find_disk(line)
		if mp is None:
			continue
		yield mp

if __name__ == "__main__":
	print "Waiting for new mounts"
	for m in udisk(debug=True):
		print m
