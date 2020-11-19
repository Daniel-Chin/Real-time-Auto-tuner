print('importing...')
import sys
import socket
from util import *
from resampy import resample
from os import system
from time import sleep
DEBUG = True
if DEBUG:
	import tkinter as tk
	from threading import Thread, Condition
PITCHER = 2334
ANALYZER = 2333
CHUNK = 1024
WINDOW_SIZE = 2 * CHUNK
FILTER = 'kaiser_fast'
BEND_SMOOTH = 10 

def main():
	print('MAIN')
	system('title pitcher')
	init()
	try:
		while True:
			sleep(.2)
			print('*' * (next(getDelta)//16))
	finally:
		print('I was pitcher')

def init():
	global getDelta
	# preperations
	print('init...')
	getDelta = GetDelta()
	if DEBUG:
		class GUI(Thread):
			def __init__(self, condition):
				Thread.__init__(self)
				self.intVar = None
				self.condition = condition
				self.root = None
			
			def getIntVar(self):
				return self.intVar
			
			def onClose(self):
				self.intVar = None
				self.root.destroy()
			
			def run(self):
				with self.condition:
					root = tk.Tk()
					self.intVar = tk.IntVar()
					condition.notify()
				scale = tk.Scale(root, to = 0, from_ = 255, resolution = 1, 
								variable = self.intVar)
				scale.set(128)
				scale.pack()
				root.title('Pitcher GUI')
				root.protocol('WM_DELETE_WINDOW', self.onClose)
				self.root = root
				print('mainloop...')
				root.mainloop()
				del self.root
		
		global getIntVar
		condition = Condition()
		gui = GUI(condition)
		with condition:
			gui.start()
			while gui.getIntVar() is None:
				condition.wait()
			getIntVar = gui.getIntVar
	print('START')

def GetDelta():
	delta = 128
	to_fix = 128
	while True:
		if DEBUG:
			delta = getIntVar().get()
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
	freq_ratio = 2 ** ((delta - 128) / 256 / 12)
	len_chunk = len(chunk)
	if freq_ratio > 1:
		# sharper
		chunk = resample(chunk, 44100, 44100 // freq_ratio, filter=FILTER)
		return chunk + chunk[len(chunk) - len_chunk:]
	else:
		# flatter
		chunk = chunk[:int(len_chunk * freq_ratio)]
		chunk = resample(chunk, 44100, 44100 // freq_ratio, filter=FILTER)
		if len(chunk) < len_chunk:
			return chunk + chunk[-1:] * (len_chunk - len(chunk))
		else:
			return chunk[:len_chunk]

main()
sys.exit(0)
