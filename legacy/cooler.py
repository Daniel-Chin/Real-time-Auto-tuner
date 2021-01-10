print('importing...')
import sys
import socket
from util import *
from numpy import fromstring, int16, float32, rint, zeros, array
PITCHER = 2334
ANALYZER = 2333
SPEAKER = 2335
PAGE = 1024
PIPE_PAGE = 2 * PAGE

DELAY_SEC = .25
DECAY = .25
N_ECHOS = 3
EASY = 1.2

BEND_SMOOTH = 10 
ANTI_CLIP = .99 # For performance, we don't normalize. 
# To prevent wave value > int16, we multiply everything with `ANTI_CLIP`. 
BUFFER_PRECISION = float32
SCORE_BUFFER_SIZE = int(44100 / PAGE) * 3

def main():
	print('MAIN')
	title('cooler')
	init()
	try:
		while True:
			last_data = b''
			data = b''
			try:
				data = sockPitcher.recv(PIPE_PAGE)
				while len(data) == PIPE_PAGE:
					last_data = data
					data = sockPitcher.recv(PIPE_PAGE)
					congestPitcher()
				if len(data) % 2 == 1:
					data += recvall(sockPitcher, 1)
				data = last_data[len(data) - PIPE_PAGE:] + data
			except BlockingIOError:
				pass
			if len(data) < PIPE_PAGE:
				data += recvall(sockPitcher, PIPE_PAGE - len(data))
			
			freshman = fromstring(data, dtype = int16) * amp_ratio
			campus = rint(freshman + buffer.pop(0).sum(axis = 0)).astype(int16)
			
			sockSpeaker.sendall(campus.data.tobytes())
			
			score = next(getScore)
			buffer.append(zeros([N_ECHOS, PAGE]))
			for i in range(N_ECHOS):
				buffer[(i + 1) * delay_page - 1][i] = freshman * \
					exp_lookup[i] * score
	finally:
		force(sockPitcher.close)
		force(sockAnalyzer.close)
		force(sockSpeaker.close)
		print('I was cooler')

def init():
	global sockAnalyzer, sockPitcher, sockSpeaker, congestAnalyzer, \
		congestPitcher, exp_lookup, amp_ratio, delay_page, \
		buffer_page, buffer, getScore
	sockAnalyzer = socket.socket()
	print('connecting analyzer...', end = '\r')
	sockAnalyzer.connect(('localhost', ANALYZER))
	sockAnalyzer.sendall(b'coo')
	print('analyzer ONLINE.      ')
	sockAnalyzer.setblocking(False)

	sockPitcher = socket.socket()
	print('connecting pithcer...', end = '\r')
	sockPitcher.connect(('localhost', PITCHER))
	sockPitcher.sendall(b'coo')
	print('pithcer ONLINE.      ')
	sockPitcher.setblocking(False)

	sockSpeaker = socket.socket()
	print('connecting speaker...', end = '\r')
	sockSpeaker.connect(('localhost', SPEAKER))
	sockSpeaker.sendall(b'coo')
	print('speaker ONLINE.      ')
	# preperations
	print('init...')
	getScore = GetScore()
	congestAnalyzer = CongestionAnalyzer('Score').acc
	congestPitcher = CongestionAnalyzer('WavetoCool').acc
	exp_lookup = array(tuple(DECAY ** x for x in range(1, N_ECHOS + 1)), dtype = BUFFER_PRECISION)
	amp_ratio = BUFFER_PRECISION(1. / (1. + sum(exp_lookup)) * ANTI_CLIP)
	delay_page = int((DELAY_SEC * 44100) // PAGE)
	buffer_page = delay_page * N_ECHOS
	buffer = [zeros([N_ECHOS, PAGE]) for _ in range(buffer_page)]
	print('Good to go. Waiting for START signal...')
	assert recvall(sockPitcher, 5) == b'START'
	sockSpeaker.sendall(b'START')
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
