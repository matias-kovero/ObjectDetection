import cv2 as cv
from time import time
from wincap import WinCap
import keyboard
import mouse

# initialize wincap
wincap = WinCap(None, 640, True)

# State
STOP='f12'
GATHER='f10'
gatherDataset = False
active = True
last_ss = time()

def on_stop():
  global active
  active = False
  print('Stopping code!')

def toggleGather():
  global gatherDataset
  gatherDataset = not gatherDataset
  if gatherDataset:
    print('Gathering dataset to folder: ./images/')
  else:
    print('Stopped gathering. Resume with {}'.format(GATHER))

def take_ss():
  global last_ss, gatherDataset
  if (gatherDataset and time() - last_ss > 10): # 10s cooldown on ss
    last_ss = time()
    wincap.save_ss()

# Hooks
keyboard.add_hotkey(STOP, on_stop)
keyboard.add_hotkey(GATHER, toggleGather)
# mouse.on_click(take_ss) # this would fire after button is raised up again - it is abit too late.
mouse.on_button(take_ss, buttons=[mouse.LEFT], types=[mouse.DOWN])

print('STOP = {}'.format(STOP))
print('Toggle Gather = {}'.format(GATHER))

while(active):
  # press 'q' to exit
  # waits 25ms every loop to process key press
  if cv.waitKey(25) & 0xFF == ord('q'):
    cv.destroyAllWindows()
    break

cv.destroyAllWindows()
print('End.')