print('importing...')
import pyaudio
from time import time
from yin import yin
import numpy as np
from resampy import resample

SR = 44100
FRAME_LEN = 2048
DTYPE = (np.float32, pyaudio.paFloat32)
FILTER = 'kaiser_best'

def main():
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format = DTYPE[1], channels = 1, rate = SR, 
        input = True, frames_per_buffer = FRAME_LEN,
    )
    streamOut = pa.open(
        format = DTYPE[1], channels = 1, rate = SR, 
        output = True, frames_per_buffer = FRAME_LEN,
    )
    try:
        print('autotune()')
        autotune(stream, streamOut)
        # relay(stream, streamOut)
    except KeyboardInterrupt:
        print('Ctrl+C received. Shutting down. ')
    finally:
        stream.stop_stream()
        stream.close()
        streamOut.stop_stream()
        streamOut.close()
        pa.terminate()
        print('Resources released. ')

def autotune(stream, streamOut):
    display_time = 0
    while True:
        time_start = time()
        frame, waste = getLatestFrame(stream)
        idle_time = time() - time_start

        time_start = time()
        f0 = yin(frame, SR, FRAME_LEN)
        pitch = np.log(f0) * 17.312340490667562 - 36.37631656229591
        f0_time = time() - time_start

        time_start = time()
        frame, pitch_to_bend = pitchBend(frame, f0)
        bender_time = time() - time_start

        time_start = time()
        streamOut.write(frame, FRAME_LEN)
        write_time = time() - time_start

        time_start = time()
        display(
            idle_time, f0_time, bender_time, write_time,
            display_time, pitch_to_bend,
        )
        display_time = time() - time_start

def getLatestFrame(stream):
    waste = stream.get_read_available() - FRAME_LEN
    if waste > 0:
        stream.read(waste)
    return np.frombuffer(
        stream.read(FRAME_LEN), dtype = DTYPE[0]
    ), waste

def pitchBend(frame, its_pitch):
    pitch_to_bend = - its_pitch % 3
    if pitch_to_bend < -1.5:
        pitch_to_bend += 3
    if pitch_to_bend == 0:
        return frame, 0
    freq_oitar = np.exp(- pitch_to_bend * 0.057762265046662105)
    # The inverse of 'ratio'
    if freq_oitar < 1.0:
        # sharper
        frame = resample(frame, SR, SR * freq_oitar, filter=FILTER)
        return np.append(frame, frame[frame.size - FRAME_LEN:]), pitch_to_bend
    else:
        # flatter
        frame = frame[:FRAME_LEN // freq_oitar]
        frame = resample(frame, SR, SR * freq_oitar, filter=FILTER)
        if frame.size < FRAME_LEN:
            return np.append(frame, frame[frame.size - FRAME_LEN:]), pitch_to_bend
        else:
            return frame[:FRAME_LEN], pitch_to_bend

def display(
    idle_time, f0_time, bender_time, write_time, 
    display_time, pitch_to_bend, 
):
    print(pitch_to_bend)

def relay(stream, streamOut):
    while True:
        frame, waste = getLatestFrame(stream)
        streamOut.write(frame, FRAME_LEN)
        print(waste)

main()
