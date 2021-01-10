print('importing...')
import wave
import sys
import numpy as np
from resampy import resample
from console import console
delta = int(input('delta='))
FILTER = 'kaiser_fast'
WINDOW = 4096

def main():
    print('MAIN')
    f = wave.openfp('0.wav')
    data = f.readframes(f.getnframes())
    framerate = f.getframerate()
    assert 2 == f.getsampwidth()
    f.close()
    frames = (np.fromstring(data, dtype = np.int16).astype(np.float32)/32768.0)
    if 1:
        frames = frames[:(len(frames) // WINDOW) * WINDOW]
        chunks = np.split(frames, len(frames)//WINDOW)
        new_chunks = [pitchBend(x) for x in chunks]
    else:
        frames = pitchBend(frames)
        frames = frames[:(len(frames) // WINDOW) * WINDOW]
        new_chunks = np.split(frames, len(frames)//WINDOW)
    f = wave.openfp('1.wav', 'wb')
    f.setframerate(framerate)
    f.setnchannels(1)
    f.setsampwidth(2)
    [f.writeframes(np.rint(x*32768).astype(np.int16).data.tobytes()) 
     for x in new_chunks]
    f.close()

def pitchBend(chunk):
    if delta == 128:
        return chunk
    freq_ratio = 2. ** ((delta - 128) / 256 / 12)
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
