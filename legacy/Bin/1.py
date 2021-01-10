print('importing...')
import sys
import pyaudio
import wave
import IPython
from io import BytesIO as IO
from threading import Lock
from numpy import sinc
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME = "1.wav"
ANTI_CLICK = 0

class PoorBender:
	'''
	No Fourier. Square window. Sinc. 
	'''
	def __init__(self, stream):
		self.stream = stream
		self.buffer = IO()
		self.__bend = 0
		self.lockBend = Lock()
		self.win_size = RATE / 20

	def setBend(new_bend):
		with self.lockBend:
			self.__bend = new_bend

	def getBend():
		with self.lockBend:
			return self.__bend

	def write(data):
		pass

def main():
	global pa
	pa = pyaudio.PyAudio()
	frames = []

	# start Recording
	oStream = pa.open(format=FORMAT, channels=CHANNELS,
	                rate=RATE, output=True)
	iStream = pa.open(format=FORMAT, channels=CHANNELS,
	                rate=RATE, input=True,
	                frames_per_buffer=CHUNK)

	print("recording...")
	for i in range(RATE * RECORD_SECONDS // CHUNK):
		data = iStream.read(CHUNK)
		if i > ANTI_CLICK:
			frames.append(data)
	print("finished recording")

	# stop Recording
	iStream.stop_stream()
	iStream.close()

	print('Playing...')
	oStream.write(b''.join(frames))
	oStream.stop_stream()
	oStream.close()
	pa.terminate()

	waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
	waveFile.setnchannels(CHANNELS)
	waveFile.setsampwidth(pa.get_sample_size(FORMAT))
	waveFile.setframerate(RATE)
	waveFile.writeframes(b''.join(frames))
	waveFile.close()

	#IPython.embed()

if __name__ == '__main__':
	main()
	sys.exit(0)
