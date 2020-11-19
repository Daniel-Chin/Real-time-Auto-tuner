print('importing...')
import sys
import pyaudio
from pyaudio import paInt8, paInt16
import socket
from util import *
SPEAKER = 2335
CHUNK = 1024
PAGE = 2048

def main():
	print('MAIN')
	title('speaker')
	init()
	try:
		residu = b''
		while True:
			last_data = b''
			data = b''
			try:
				data = sockCooler.recv(PAGE)
				while len(data) == PAGE:
					last_data = data
					data = sockCooler.recv(PAGE)
					congest()
				if len(data) % 2 == 1:
					data += recvall(sockCooler, 1)
				data = last_data[len(data) - PAGE:] + data
			except BlockingIOError:
				pass
			if len(data) < PAGE:
				data += recvall(sockCooler, PAGE - len(data))
			
			stream.write(data)
	finally:
		force(sockCooler.close)
		force(serverSock.close)
		stream.stop_stream()
		stream.close()
		pa.terminate()
		print('I was speaker')

def init():
	global sockCooler, serverSock, pa, stream, congest
	serverSock = socket.socket()
	serverSock.bind(('localhost', SPEAKER))
	serverSock.listen(1)
	print('connecting cooler...', end = '\r')
	sockCooler, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockCooler, 3) == b'coo'
	print('cooler ONLINE.      ')
	sockCooler.setblocking(False)

	print('init...')
	CA = CongestionAnalyzer('Speaker')
	congest = CA.acc
	pa = pyaudio.PyAudio()
	stream = pa.open(format = paInt16, channels = 1,
        rate = 44100, output = True, frames_per_buffer = CHUNK)
	print('Good to go. Waiting for START signal...')
	assert recvall(sockCooler, 5) == b'START'
	print('START')

main()
sys.exit(0)
