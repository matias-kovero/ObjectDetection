import cv2 as cv
from time import time

import numpy as np

# Colors - BGR
CYAN    = (255, 255,   0)
YELLOW  = (  0, 255, 255)
ORANGE  = (  0, 132, 255)
RED     = (  0,   0, 255)
GREEN   = (  0, 255,   0)
PURPLE  = (255,   0, 255)

class Screen:
  """
  If debug is turned on, to close screen -> focus screen and press Q
  """
  # properties
  name = 'Screen'
  pipe_result = None
  pipe_mouse = None
  running = False
  source = 0
  previous = None
  prev_dist = 0
  debug = False
  # constructor
  def __init__(self, out_result, in_mouse, source, debug=False) -> None:
    print(f'[{self.name}] Process launched.')
    # keyboard.add_hotkey(kill_switch, self.cleanup)
    # Pipes
    self.pipe_result = out_result
    self.pipe_mouse = in_mouse
    # Screen size
    self.source = source
    # Show inference results - this will hinder FPS - should only use when debuging.
    self.debug = debug

    self.run()
    pass

  def run(self):
    self.running = True
    last_time = time()
    while self.running:
      try:
        (result, img, model_time) = self.pipe_result.recv()
        self.find_aid(result)

        if self.debug:
          if result is not None: 
            self.plot_boxes(img, result)
          cv.putText(img, f'{1/(time()-last_time):.1f} FPS | {model_time:.0f}ms', (2, 15), cv.FONT_HERSHEY_COMPLEX_SMALL, 0.65, CYAN)
          cv.imshow('Yolo Debug', img)
          last_time = time()
          # This will mess up mouse capture - don't close with this - close by killing process.
          if cv.waitKey(1) & 0xFF == ord('q'):
            break
      except EOFError:
        break

    cv.destroyAllWindows()
    print(f'[{self.name}] Main Thread ended.')

  def cleanup(self):
    print(f'[{self.name}] Cleanup.')
    self.running = False

  def plot_boxes(self, frame, pos):
    """
    Plots boxes and labels on frame.
    :param frame: frame on which to make plots
    :param pos: inferences made by model
    :return: new frame with boxes and labels plotted
    """
    # We could check all results, and only render one that is the closest
    rect_center = (int((pos[0]+pos[2]) / 2), int((pos[1]+pos[3]) / 2))
    width = int(pos[2] - pos[0])
    offset = int((pos[3]-pos[1]) * 0.3) # 0.5 would be top
    height = max(60, offset)
    # Put rectangle around our object
    cv.rectangle(frame, (int(pos[0]), int(pos[1])), (int(pos[2]), int(pos[3])), CYAN, 2)
    # Outer slow section
    """ cv.rectangle(frame, 
      (int(rect_center[0] - (width / 2)), int(rect_center[1] - offset - (height / 2))), 
      (int(rect_center[0] + (width / 2)), int(rect_center[1] - offset + (height / 2))), 
    YELLOW, 2)
    # Medium slow down
    cv.rectangle(frame, 
      (int(rect_center[0] - (width * 0.75 / 2)), int(rect_center[1] - offset - (height * 0.75 / 2))), 
      (int(rect_center[0] + (width * 0.75 / 2)), int(rect_center[1] - offset + (height * 0.75 / 2))), 
    ORANGE, 2)
    # Major slow down
    cv.rectangle(frame, 
      (int(rect_center[0] - (width * 0.45 / 2)), int(rect_center[1] - offset - (height * 0.45 / 2))), 
      (int(rect_center[0] + (width * 0.45 / 2)), int(rect_center[1] - offset + (height * 0.45 / 2))), 
    RED, 2) """
    # Get text size
    (txt_w, txt_h), baseline = cv.getTextSize(f'{pos[4]:.2f}', cv.FONT_HERSHEY_COMPLEX_SMALL, 0.5, 1)
    # Text rectangle
    cv.rectangle(frame, (int(pos[0]), int(pos[1])), (int(pos[0]) + txt_w, int(pos[1]) - txt_h - baseline), CYAN, cv.FILLED)
    # Put text above rectangle
    cv.putText(frame, f'{pos[4]:.2f}', (int(pos[0]), int(pos[1] - 3)), cv.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0,0,0))
    # Center - Point of Intrest
    frame_center = int(self.source / 2)
    # print(self.pythagoreanTheorem(rect_center[0] - frame_center, rect_center[1] - frame_center))
    cv.circle(frame, (rect_center[0], rect_center[1] - offset), 3, GREEN, 2, cv.FILLED)
    # draw line from POI to screen center
    cv.line(frame, (rect_center[0], rect_center[1] - offset), (frame_center, frame_center), YELLOW, 1)
    return frame

  def find_aid(self, pos):
    # If data has not changed -> return
    if self.previous is pos:
      return
    # Some logic to update if going from x, y to None. After that don't update future None
    if pos is None:
      self.pipe_mouse.send(( (0,0), (0,0), 0) )
      self.previous = None
    else:
      # This is getting spammed... 
      rect_center = (int((pos[0]+pos[2]) / 2), int((pos[1]+pos[3]) / 2))
      width = int(pos[2] - pos[0])
      offset = int((pos[3]-pos[1]) * 0.3)
      height = max(30, offset)
      screen_center = int(self.source / 2)
      # These are the actual coords, or distace from center
      x = rect_center[0] - screen_center
      y = rect_center[1] - offset - screen_center
      move = (x, -y) # Flip - as these are in top-left (0,0) = -up | +down but mouse is +up, -down
      size = (width, height)
      dist = self.rect_distance(x, y)
      if (abs(self.prev_dist - dist) > 3): #or ((int(self.prev_dist) ^ int(dist)) < 0)):
        self.pipe_mouse.send((move, size, dist))
        self.prev_dist = dist
        self.previous = move
    
  def rect_distance(self, x, y):
    return np.sqrt(abs(x)**2 + abs(y)**2)