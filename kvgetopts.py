#!/usr/bin/env python

def coerce_bool(value):
	if isinstance(value,(str,unicode)):
		if "false" in value or "False" in value or "off" in value:
			value = False
		elif "true" in value or "True" in value or "on" in value:
			value = True
	return bool(value)

def coerce_int(value):
	return int(value)

class kvgetopts(object):
	def __init__(self,argv,debug=False,startindex=1):
 
		self.debug=debug
		self.args = {}
		self.remains = []
		for a in argv[0:startindex]:
			self.remains.append(a)
		for a in argv[startindex:]:
			e=a.find("=")
			if e == -1:
				if debug: print("Unrecognized argument {}, will return it".format(a))
				self.remains.append(a)
				continue
			try:
				v=int(a[e+1:])
			except:
				v=a[e+1:]
			k=a[0:e]
			if k in self.args:
				if debug: print("Duplicate argument key {}".format(k))
				tmp = self.args[k]
				if not isinstance(tmp,list):
					tmp = [ tmp ]
				tmp.append(v)
				v = tmp
			self.args[k] = v

	def __iter__(self):
		for k in self.args:
			yield k

	def __getitem__(self, attr):
		return self.args[attr]

	def get(self,k,v=None):
		if k in self.args:
			return self.args[k]
		else:
			return v


if __name__ == "__main__":
	from sys import argv
	if len(argv) > 1:
		myargv=argv
	else:
		myargv=[argv[0], "hello", "world", "hello=1", "hello=world", "you=fiend"]
	
	kv=kvgetopts(myargv,debug=True)
	myargv=kv.remains
	for k in kv:
		v=kv[k]
		print("key:{} = value:{}".format(k,v))
	print(kv.get("hello","default"))
	print(kv.get("nonesuch","default"))
	print(kv.get("nonesuch"))

	print("Remaining args: {}".format(myargv))
