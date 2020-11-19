import platform
from os import system
from time import time
__all__ = ['recvall', 'force', 'title', 'CongestionAnalyzer']

def recvall(socket, length):
	# socket must be non-blocking. 
	timeout = socket.gettimeout()
	socket.settimeout(None)
	to_recv = length
	chunk = b''
	while to_recv:
		data = socket.recv(to_recv)
		to_recv -= len(data)
		chunk += data
	socket.settimeout(timeout)
	return data

#===============================================================================
# def recvall(socket, length):
# 	# socket must be non-blocking. 
# 	to_recv = length
# 	chunk = b''
# 	while to_recv:
# 		try:
# 			data = socket.recv(to_recv)
# 			to_recv -= len(data)
# 			chunk += data
# 		except BlockingIOError:
# 			pass
# 	return data
#===============================================================================

def force(function, *args):
	try:
		function(*args)
	except Exception as e:
		print(e)

def title(text):
	if platform.system() == 'Windows':
		system('title ' + text)
	elif platform.system() == 'Darwin':
		system('echo -n -e "\033]0;%s\007"' % text)
	else:
		assert False, 'Unknown platform'

class CongestionAnalyzer:
	def __init__(self, name = ''):
		self.last_time = time()
		self.count = 0
		self.name = name
	
	def acc(self, count = 1):
		self.count += count
		delta_time = time() - self.last_time 
		if delta_time > 1:
			if self.count != 0:
				print(self.name, 'Congestion:', 
					format(count/delta_time, '.2'), 'chunks/sec')
			self.last_time = time()
			self.count = 0
