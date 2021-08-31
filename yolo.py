import cv2 as cv
from torch import hub
import numpy as np

# Colors - BGR
CYAN    = (255, 255,   0)

class Yolo:
  # properties
  name = 'YOLOv5 Model'
  img_output = None
  running = False
  screen_center = 0
  # constructor
  def __init__(self, out_frame, in_result, model, img, source) -> None:
    print(f'[{self.name}] Process launched.')
    # Pipes
    self.pipe_frame = out_frame
    self.pipe_result = in_result

    self.model = self.load_model(model)   # Load Model
    self.model.conf = 0.6                 # Model threshold
    self.model.iou = 0.65                 # NMS IoU threshold
    self.model.max_det = 3                # Maximum number of detections per img
    self.size = img                       # Inference resolution [1:1]
    self.screen_center = int(source / 2)  # Screen center [1:1] resolutions
    self.run()
    pass

  def run(self):
    """
    Main loop of our class
    """
    self.running = True
    while self.running:
      try:
        img = self.pipe_frame.recv()
        (result, model_time) = self.score_frame(img)
        # Big oof - Windows does not support multiprocessing on tensors !!! 5h wasted...
        # Quick fix - parse tensor and pipe parsed results - hope this does not hider performance.
        if len(result) >= 1:
          self.pipe_result.send((self.filter_closest(result), img, model_time))
        else:
          self.pipe_result.send((None, img, model_time))
      except (EOFError, BrokenPipeError) as e:
        break
    print(f'[{self.name}] Main Thread ended.')

  def cleanup(self):
    """
    If any cleaning is needed, its done here
    """
    print(f'[{self.name}] Cleanup.')
    self.running = False
  
  def load_model(self, path):
    """
    Function loads the yolo5 model from PyTorch Hub.
    :param self: class object
    :param path: custom model path
    """
    model = hub.load('ultralytics/yolov5', 'custom', path)
    return model

  def score_frame(self, frame):
    """
    Function scores each frame and returns results.
    :param frame: frame to be infered.
    """
    result = self.model(cv.cvtColor(frame, cv.COLOR_RGB2BGR), size=self.size)
    return (result.xyxy[0], result.t[1])

  def filter_closest(self, results):
    """
    Get the closest match to screen middle, should add check on FP from the Model to avoid quick flicks.
    """
    if len(results) <= 1: return results[0].tolist()
    # Giving 2*width, any object found should be closer.
    closest = ( self.screen_center * 2, results[0])

    for i in range(len(results)):
      pos = results[i].detach()
      # We are calculating this at screen as well, should we just send results from here through the pipe?
      # Is it better to keep pipe data small, or save computation?
      rect_center = (int((pos[0]+pos[2]) / 2), int((pos[1]+pos[3]) / 2))
      distance = self.e_distance(*rect_center, self.screen_center, self.screen_center)
      # Check if new closest
      if distance < closest[0]:
        closest = ( distance, results[i])
    return closest[1].tolist()
  
  def e_distance(self, q1,q2,p1,p2):
    return np.sqrt((q1 - p1)**2 + (q2 - p2)**2)

  def p_distance(self, x, y):
    return np.sqrt(abs(x)**2 + abs(y)**2)