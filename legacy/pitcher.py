print('importing...')
import sys
import socket
from util import *
from resampy import resample
from numpy import fromstring, int16, float32, rint, append
from time import time
PITCHER = 2334
ANALYZER = 2333
CHUNK = 1024
WINDOW_SIZE = 2 * CHUNK
assert WINDOW_SIZE % 2 == 0
FILTER = 'kaiser_fast'
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 
BEND_SMOOTH = 10 

def main():
	print('MAIN')
	title('pitcher')
	init()
	try:
		last_time = time()
		while True:
			if time() - last_time < 1:
				for i in range(8):
					sockCooler.sendall(rint(pitchBend(fromstring(recvall(
						sockRecorder, WINDOW_SIZE), dtype = int16).astype(
						float32) / 32768.0) * 32768).astype(
						int16).data.tobytes())
			else:
				last_time = time()

				last_data = b''
				data = b''
				try:
					data = sockRecorder.recv(WINDOW_SIZE)
					while len(data) == WINDOW_SIZE:
						last_data = data
						data = sockRecorder.recv(WINDOW_SIZE)
						congestRecorder()
					if len(data) % 2 == 1:
						data += recvall(sockRecorder, 1)
					data = last_data[len(data) - WINDOW_SIZE:] + data
				except BlockingIOError:
					pass
				if len(data) < WINDOW_SIZE:
					data += recvall(sockRecorder, WINDOW_SIZE - len(data))

				sockCooler.sendall(rint(pitchBend(fromstring(
					data, dtype = int16).astype(float32)
					/ 32768.0) * 32768).astype(int16).data.tobytes())
	finally:
		force(sockRecorder.close)
		force(sockAnalyzer.close)
		force(sockCooler.close)
		force(serverSock.close)
		print('I was pitcher')

def init():
	global sockAnalyzer, sockRecorder, sockCooler, serverSock, getDelta, \
		congestAnalyzer, congestRecorder
	sockAnalyzer = socket.socket()
	print('connecting analyzer...', end = '\r')
	sockAnalyzer.connect(('localhost', ANALYZER))
	sockAnalyzer.sendall(b'pit')
	print('analyzer ONLINE.      ')

	serverSock = socket.socket()
	serverSock.bind(('localhost', PITCHER))
	serverSock.listen(2)
	
	print('connecting recorder...', end = '\r')
	sockRecorder, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockRecorder, 3) == b'rec'
	print('recorder ONLINE.      ')

	print('connecting cooler...', end = '\r')
	sockCooler, addr = serverSock.accept()
	assert addr[0] == '127.0.0.1'
	assert recvall(sockCooler, 3) == b'coo'
	print('cooler ONLINE.      ')
	
	# preperations
	print('init...')
	sockAnalyzer.setblocking(False)
	sockRecorder.setblocking(False)
	getDelta = GetDelta()
	congestAnalyzer = CongestionAnalyzer('Pitch').acc
	congestRecorder = CongestionAnalyzer('WavetoPitch').acc
	print('Good to go. Waiting for START signal...')
	assert recvall(sockRecorder, 5) == b'START'
	sockCooler.sendall(b'START')
	print('START')

def GetDelta():
	delta = 128
	to_fix = 128
	tolerance = 256
	while True:
		try:
			data = sockAnalyzer.recv(tolerance)
			congestAnalyzer(len(data) - 1)
			delta = data[-1]
			bar = 16 - round(delta / 16)
			if bar < 8:
				print(' ' * bar, '-' * (8-bar), '|', ' '*8, sep = '', 
					end = '\r', flush = True)
			else:
				print(' ' * 8, '|', '+' * (bar-8), ' '*(16-bar), sep = '', 
					end = '\r', flush = True)
		except BlockingIOError:
			pass
		if abs(to_fix - delta) < BEND_SMOOTH:
			to_fix = delta
		else:
			if delta > to_fix:
				to_fix += BEND_SMOOTH
			else:
				to_fix -= BEND_SMOOTH
		yield to_fix

def pitchBend(chunk):
	delta = next(getDelta)
	if delta == 128:
		return chunk
	freq_ratio = 2. ** ((delta - 128) / 256 / 12)
	# freq_ratio = 2. ** ((delta - 128) / 256 / 6)
	len_chunk = len(chunk)
	if freq_ratio > 1:
		# sharper
		chunk = resample(chunk, 44100, 44100 // freq_ratio, filter=FILTER)
		return append(chunk, chunk[len(chunk) - len_chunk:])
	else:
		# flatter
		chunk = chunk[:int(len_chunk * freq_ratio)]
		chunk = resample(chunk, 44100, 44100 // freq_ratio, filter=FILTER)
		if len(chunk) < len_chunk:
			return append(chunk, chunk[len(chunk) - len_chunk:])
		else:
			return chunk[:len_chunk]

main()
sys.exit(0)
