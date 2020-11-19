'''
This is a debugger. The real analyzer is "analyzer copy.py"
'''
print('''WARNING: This is a debugger. The real analyzer is "analyzer copy.py"''')
print('importing...')
import sys
import socket
from util import *
from threading import Thread
from time import sleep
PITCHER = 2334
ANALYZER = 2333
WINDOW_SIZE = 4096

class Taker(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.value = 128

	def get(self):
		return self.value

	def run(self):
		while True:
			self.value = int(input('new='))

def main():
	print('MAIN')
	title('analyzer')
	init()
	try:
		taker = Taker()
		taker.start()
		while True:
			last_data = b''
			data = b''
			try:
				data = sockRecorder.recv(WINDOW_SIZE)
				while len(data) == WINDOW_SIZE:
					last_data = data
					data = sockRecorder.recv(WINDOW_SIZE)
					congest()
				data = (last_data + data)[-WINDOW_SIZE:]
			except BlockingIOError:
				pass
			if len(data) < WINDOW_SIZE:
				data += recvall(sockRecorder, WINDOW_SIZE - len(data))
			value = taker.get()
			sockPitcher.sendall(bytes([value]))
			sockCooler.sendall(bytes([value]))
	finally:
		force(sockRecorder.close)
		force(sockPitcher.close)
		force(sockCooler.close)
		force(sockGUI.close)
		force(serverSock.close)
		print('I was analyzer')

def init():
	global sockRecorder, sockPitcher, sockCooler, sockGUI, serverSock, \
		congest
	serverSock = socket.socket()
	serverSock.bind(('localhost', ANALYZER))
	serverSock.listen(4)
	
	print('connecting pitcher...', end = '\r')
	sockPitcher, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockPitcher, 3) == b'pit'
	print('pitcher ONLINE.      ')
	
	print('connecting recorder...', end = '\r')
	sockRecorder, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockRecorder, 3) == b'rec'
	print('recorder ONLINE.      ')
	sockRecorder.setblocking(False)

	print('connecting cooler...', end = '\r')
	sockCooler, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockCooler, 3) == b'coo'
	print('cooler ONLINE.      ')
	
	print('connecting GUI...', end = '\r')
	sockGUI, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockGUI, 3) == b'gui'
	print('GUI ONLINE.      ')
	
	# Preperations
	print('init...')
	congest = CongestionAnalyzer('Analyzer').acc
	# Code goes here...
	print('Good to go. Waiting for START signal...')
	assert recvall(sockRecorder, 5) == b'START'
	sockGUI.sendall(b'START')
	print('START')

main()
sys.exit(0)
