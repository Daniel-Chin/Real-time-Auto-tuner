print('importing...')
import sys
import socket
from util import *
from numpy import fromstring, int8, float16, log
from yin import estimateF0
PITCHER = 2334
ANALYZER = 2333
WINDOW_SIZE = 4096

def main():
	print('MAIN')
	title('analyzer')
	init()
	try:
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
			
			page = fromstring(data, dtype = int8).astype(float16) / 128.0
			# `page` is a WINDOW_SIZE long array of float16 between -1 and 1. 
			f0 = estimateF0(page, WINDOW_SIZE, 44100)
			pitch = log(f0) * 17.312340490667562 - 36.37631656229591
			residu = pitch % 1
			# chroma = round(pitch) % 12
			# symbol = [
			# 	'C ', 'C#', 
			# 	'D ', 'D#', 
			# 	'E ', 
			# 	'F ', 'F#', 
			# 	'G ', 'G#', 
			# 	'A ', 'A#', 
			# 	'B ',
			# ][chroma]
			# print(' ', symbol, '#' * round(residu * 20), ' ' * 18, end='\r', flush=True)
			if residu > .5:
				residu -= 1
			score = 128 - round(255 * residu)

			# tone = pitch % 12
			# if tone < 1:
			# 	diatone = 0
			# elif tone < 3:
			# 	diatone = 2
			# elif tone < 4.5:
			# 	diatone = 4
			# elif tone < 6:
			# 	diatone = 5
			# elif tone < 8:
			# 	diatone = 7
			# elif tone < 10:
			# 	diatone = 9
			# elif tone < 11.5:
			# 	diatone = 11
			# else:
			# 	diatone = 12
			# score = round(255 * (diatone - tone)/2) + 128
			
			sockPitcher.sendall(bytes([score]))
			sockCooler.sendall(bytes([score]))
	finally:
		force(sockRecorder.close)
		force(sockPitcher.close)
		force(sockCooler.close)
		#force(sockGUI.close)
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
	'''
	print('connecting GUI...', end = '\r')
	sockGUI, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockGUI, 3) == b'gui'
	print('GUI ONLINE.      ')
	'''
	# Preperations
	print('init...')
	congest = CongestionAnalyzer('Analyzer').acc
	# Code goes here...
	print('Good to go. Waiting for START signal...')
	assert recvall(sockRecorder, 5) == b'START'
	#sockGUI.sendall(b'START')
	print('START')

main()
sys.exit(0)
