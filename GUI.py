print('importing...')
import sys
import socket
from util import *
ANALYZER = 2333

WIDTH = 64
HEIGHT = 18

def main():
	print('MAIN')
	title('GUI')
	init()
	try:
		score = next(getScore)
		
	finally:
		force(sockAnalyzer.close)
		print('I was GUI')

def init():
	global sockAnalyzer, getScore
	sockAnalyzer = socket.socket()
	print('connecting analyzer...', end = '\r')
	sockAnalyzer.connect(('localhost', ANALYZER))
	sockAnalyzer.sendall(b'coo')
	print('analyzer ONLINE.      ')
	sockAnalyzer.setblocking(False)

	# preperations
	print('init...')
	getScore = GetScore()
	print('Good to go. Waiting for START signal...')
	assert recvall(sockAnalyzer, 5) == b'START'
	print('START')

def GetScore():
	delta = 128
	to_fix = 128
	tolerance = 256
	buffer = [1] * SCORE_BUFFER_SIZE
	while True:
		try:
			data = sockAnalyzer.recv(tolerance)
			congestAnalyzer(len(data) - 1)
			delta = data[-1]
		except BlockingIOError:
			pass
		if abs(to_fix - delta) < BEND_SMOOTH:
			to_fix = delta
		else:
			if delta > to_fix:
				to_fix += BEND_SMOOTH
			else:
				to_fix -= BEND_SMOOTH
		buffer.pop(0)
		buffer.append(1 - abs(to_fix - 128) * 0.0078125)
		yield min(sum(buffer) / SCORE_BUFFER_SIZE * EASY, 1.)

main()
sys.exit(0)
