print('importing...')
import sys
import pyaudio
from pyaudio import paInt8, paInt16
import socket
from util import *
PITCHER = 2334
ANALYZER = 2333
CHUNK = 1024

def main():
	print('MAIN')
	title('recorder')
	init()
	stream = pa.open(format = paInt16, channels = 1,
        rate = 44100, input = True, frames_per_buffer = CHUNK)

	try:
		i = 0
		while True:
			i = (i+1) % 256
			data = stream.read(CHUNK)
			#data = bytes([i]) * (CHUNK*2)
			sockPitcher.sendall(data)
			sockAnalyzer.sendall(data[1::2])
	finally:
		stream.stop_stream()
		force(sockAnalyzer.close)
		force(sockPitcher.close)
		stream.close()
		pa.terminate()
		print('I was recorder')

def init():
	global sockPitcher, sockAnalyzer, pa
	sockAnalyzer = socket.socket()
	print('connecting analyzer...', end = '\r')
	sockAnalyzer.connect(('localhost', ANALYZER))
	sockAnalyzer.sendall(b'rec')
	print('analyzer ONLINE.      ')

	sockPitcher = socket.socket()
	print('connecting pitcher...', end = '\r')
	sockPitcher.connect(('localhost', PITCHER))
	sockPitcher.sendall(b'rec')
	print('pitcher ONLINE.      ')

	print('init...')
	pa = pyaudio.PyAudio()
	print('Good to go. ')
	input('Press ENTER to start... ')
	sockAnalyzer.sendall(b'START')
	sockPitcher.sendall(b'START')
	print('START')

main()
sys.exit(0)
