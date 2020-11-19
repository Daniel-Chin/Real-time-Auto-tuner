print('importing...')
import sys
import pyaudio
import numpy as np
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME = "1.wav"
ANTI_CLICK = 0

def main():
	pa = pyaudio.PyAudio()
	frames = []

	# start Recording
	oStream = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
	                rate=RATE, output=True)
	iStream = pa.open(format=pyaudio.paInt16, channels=CHANNELS,
	                rate=RATE, input=True,
	                frames_per_buffer=CHUNK)

	print("recording...")
	for i in range(RATE * RECORD_SECONDS // CHUNK):
		data = iStream.read(CHUNK)
		if i > ANTI_CLICK:
			frames.append(np.fromstring(data, dtype = np.int16))
	print("finished recording")

	# stop Recording
	iStream.stop_stream()
	iStream.close()

	print('Playing...')
	for frame in frames:
		oStream.write(frame.data.tobytes())
	oStream.stop_stream()
	oStream.close()
	pa.terminate()

if __name__ == '__main__':
	main()
	sys.exit(0)
