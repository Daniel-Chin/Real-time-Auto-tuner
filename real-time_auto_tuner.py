print('importing...')
import pyaudio
from time import time
from yin import yin
import numpy as np
from resampy import resample

CONFIDENCE_TIME = .1
CONFIDENCE_TIME = .00001
HYSTERESIS = .2

SR = 44100
FRAME_LEN = 1024
DTYPE = (np.float32, pyaudio.paFloat32)
# FILTER = 'kaiser_fast'
FILTER = 'kaiser_best'
FRAME_TIME = 1 / SR * FRAME_LEN
FRAME_CONFIDENCE = FRAME_TIME / CONFIDENCE_TIME

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
    classification = 0
    confidence = 0
    tolerance = HYSTERESIS
    while True:
        time_start = time()
        frame, waste = getLatestFrame(stream)
        idle_time = time() - time_start

        time_start = time()
        f0 = yin(frame, SR, FRAME_LEN)
        pitch = np.log(f0) * 17.312340490667562 - 36.37631656229591
        f0_time = time() - time_start

        time_start = time()
        loss = abs(pitch - classification) - .5
        if loss < 0:
            confidence = min(
                1, confidence + FRAME_CONFIDENCE
            )
            tolerance = HYSTERESIS
        else:
            tolerance -= loss
            if tolerance < 0:
                confidence = 0
                classification = round(pitch)
        pitch_to_bend = classification - pitch
        confident_correction = pitch_to_bend * confidence
        hysteresis_time = time() - time_start

        time_start = time()
        frame = pitchBend(frame, confident_correction)
        bender_time = time() - time_start

        time_start = time()
        streamOut.write(frame, FRAME_LEN)
        write_time = time() - time_start

        time_start = time()
        display(
            idle_time, f0_time, bender_time, write_time,
            display_time, pitch_to_bend, waste, 
            hysteresis_time, 
        )
        display_time = time() - time_start

def getLatestFrame(stream):
    waste = stream.get_read_available() - FRAME_LEN
    if waste > 0:
        stream.read(waste)
    return np.frombuffer(
        stream.read(FRAME_LEN), dtype = DTYPE[0]
    ), waste

def pitchBend(frame, pitch_to_bend):
    if pitch_to_bend == 0:
        return frame
    freq_oitar = np.exp(- pitch_to_bend * 0.057762265046662105)
    # The inverse of 'ratio'
    if freq_oitar < 1.0:
        # sharper
        frame = resample(frame, SR, SR * freq_oitar, filter=FILTER)
        return np.append(frame, frame[frame.size - FRAME_LEN:])
    else:
        # flatter
        frame = frame[:int(FRAME_LEN / freq_oitar)]
        frame = resample(frame, SR, SR * freq_oitar, filter=FILTER)
        if frame.size < FRAME_LEN:
            return np.append(frame, frame[frame.size - FRAME_LEN:])
        else:
            return frame[:FRAME_LEN]

METER_WIDTH = 50
METER = '[' + ' ' * METER_WIDTH + '|' + ' ' * METER_WIDTH + ']'
METER_CENTER = METER_WIDTH + 1
TIMES = [
    'idle_time', 'f0_time', 'hysteresis_time', 
    'bender_time', 'write_time', 'display_time', 
]
def display(
    idle_time, f0_time, bender_time, write_time, 
    display_time, pitch_to_bend, waste, hysteresis_time, 
):
    buffer_0 = [*METER]
    offset = - round(METER_WIDTH * pitch_to_bend)
    try:
        buffer_0[METER_CENTER + offset] = '#'
    except IndexError:
        print('爆表了：', pitch_to_bend)
    _locals = locals()
    print(*buffer_0, sep='')
    print('', *[x[:-5] + ' {:4.0%}.    '.format(_locals[x] / FRAME_TIME) for x in TIMES], end='')
    print('Waste:', max(0, waste))  # samples dumped

def relay(stream, streamOut):
    while True:
        frame, waste = getLatestFrame(stream)
        streamOut.write(frame, FRAME_LEN)
        print(waste)

main()
