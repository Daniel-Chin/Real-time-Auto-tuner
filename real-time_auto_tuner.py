print('importing...')
import pyaudio
from time import time, sleep
from yin import yin
import numpy as np
from resampy import resample
from queue import Queue

print('Preparing constants...')
# CONFIDENCE_TIME = .1
CONFIDENCE_TIME = .00001
HYSTERESIS = .2
FRAME_LEN = 1024
CROSS_FADE = 0.04
DO_ECHO = False

SR = 44100
DTYPE = (np.float32, pyaudio.paFloat32)
# FILTER = 'kaiser_fast'
FILTER = 'kaiser_best'
ECHO_TIMES = 6
ECHO_DECAY = -1.5
ECHO_PERIOD = .15

FRAME_TIME = 1 / SR * FRAME_LEN
FRAME_CONFIDENCE = FRAME_TIME / CONFIDENCE_TIME
CROSS_FADE_TAILS = round(FRAME_LEN * (1 - CROSS_FADE) / 2)
CROSS_FADE_OVERLAP = FRAME_LEN - 2 * CROSS_FADE_TAILS
assert CROSS_FADE_OVERLAP + 2 * CROSS_FADE_TAILS == FRAME_LEN
# Linear cross fade
FADE_IN_WINDOW = np.array([
    x / CROSS_FADE_OVERLAP for x in range(CROSS_FADE_OVERLAP)
], DTYPE[0])
FADE_OUT_WINDOW = np.flip(FADE_IN_WINDOW)
ECHO_FPP = round(ECHO_PERIOD / FRAME_TIME)

streamOutContainer = []
display_time = 0
classification = 0
confidence = 0
tolerance = HYSTERESIS
time_start = 0
echoBuffer = [
    np.zeros((FRAME_LEN, ), DTYPE[0]) 
    for _ in range(ECHO_TIMES * ECHO_FPP)
]

def main():
    pa = pyaudio.PyAudio()
    streamOutContainer.append(pa.open(
        format = DTYPE[1], channels = 1, rate = SR, 
        output = True, frames_per_buffer = FRAME_LEN,
    ))
    streamIn = pa.open(
        format = DTYPE[1], channels = 1, rate = SR, 
        input = True, frames_per_buffer = FRAME_LEN,
        stream_callback = onAudioIn, 
    )
    streamIn.start_stream()
    try:
        while streamIn.is_active():
            sleep(1)
        # relay(stream, streamOut)
    except KeyboardInterrupt:
        print('Ctrl+C received. Shutting down. ')
    finally:
        streamOutContainer[0].stop_stream()
        streamOutContainer[0].close()
        streamIn.stop_stream()
        streamIn.close()
        pa.terminate()
        print('Resources released. ')

def onAudioIn(in_data, frame_count, time_info, status):
    global display_time, classification, confidence, tolerance, time_start

    idle_time = time() - time_start

    time_start = time()
    frame = np.frombuffer(
        in_data, dtype = DTYPE[0]
    )
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
    if DO_ECHO:
        echoBuffer.append(frame)
        frame = sum([
            x * np.exp(ECHO_DECAY * (ECHO_TIMES - i)) 
            for i, x in enumerate(echoBuffer[0::ECHO_FPP])
        ])
        echoBuffer.pop(0)
    echo_time = time() - time_start

    time_start = time()
    streamOutContainer[0].write(frame, FRAME_LEN)
    write_time = time() - time_start

    time_start = time()
    display(
        f0_time, bender_time, write_time,
        display_time, pitch_to_bend, 
        hysteresis_time, idle_time, echo_time,
    )
    display_time = time() - time_start

    time_start = time()
    return (None, pyaudio.paContinue)

def pitchBend(frame, pitch_to_bend):
    if pitch_to_bend == 0:
        return frame
    freq_oitar = np.exp(- pitch_to_bend * 0.057762265046662105)
    # The inverse of 'ratio'
    frame = resample(frame, SR, SR * freq_oitar, filter=FILTER)
    left      = frame[:CROSS_FADE_TAILS]
    left_mid  = frame[CROSS_FADE_TAILS:CROSS_FADE_TAILS + CROSS_FADE_OVERLAP]
    right_mid = frame[-CROSS_FADE_TAILS - CROSS_FADE_OVERLAP:-CROSS_FADE_TAILS]
    right     = frame[-CROSS_FADE_TAILS:]
    frame = np.concatenate((
        left, 
        np.multiply(left_mid, FADE_OUT_WINDOW) 
        + np.multiply(right_mid, FADE_IN_WINDOW), 
        right,
    ))
    return frame

METER_WIDTH = 50
METER = '[' + ' ' * METER_WIDTH + '|' + ' ' * METER_WIDTH + ']'
METER_CENTER = METER_WIDTH + 1
TIMES = [
    'f0_time', 'hysteresis_time', 
    'bender_time', 'echo_time', 'write_time', 
    'display_time', 'idle_time',
]
def display(
    f0_time, bender_time, write_time, 
    display_time, pitch_to_bend, hysteresis_time, 
    idle_time, echo_time, 
):
    buffer_0 = [*METER]
    offset = - round(METER_WIDTH * pitch_to_bend)
    try:
        buffer_0[METER_CENTER + offset] = '#'
    except IndexError:
        print('爆表了：', pitch_to_bend)
    _locals = locals()
    print(*buffer_0, sep='')
    print('', *[x[:-5] + ' {:4.0%}.    '.format(_locals[x] / FRAME_TIME) for x in TIMES])

main()
