import sys
from time import sleep
from os import getcwd

seq = ['analyzer', 'pitcher', 'recorder', 'speaker', 'cooler']

if input('This is only for MacOS. Enter...') != '':
    print('exit. ')
    sys.exit(0)

from pyautogui import hotkey, typewrite, press
for name in seq:
    name += '.py'
    code = 'python3 ' + name
    hotkey('command', 'n')
    sleep(.3)
    typewrite('cd ' + getcwd())
    sleep(.1)
    press('enter')
    sleep(.1)
    typewrite(code)
    sleep(.1)
    press('enter')
    sleep(4)
