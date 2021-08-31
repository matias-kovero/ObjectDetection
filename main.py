"""
Testing multiprocessing, 
should utilize CPU cores
"""
import multiprocessing
from multiprocessing import Pipe
import argparse

# Custom Classes for processes
from yolo import Yolo
from wincap import WinCap
from inter import InterMouse
from screen import Screen

class MultiYOLO:
  """
  Testing multiprocessing benefits, will it speed things up?
  Mainly looking for paraller execution on yolo & capture
  """
  # properties
  mouse = None
  wincap = None
  screen = None
  yolo = None
  running = False
  name = 'MultiYOLOv5'

  # constructor
  def __init__(self, model, img=640, source=640, window=None, debug=False) -> None:
    print(f'[{self.name}] Loading...')
    # Pipes
    out_mouse, in_mouse = Pipe()    # Mouse info (input from yolo, output for mouse)
    out_frame, in_frame = Pipe()    # Screen capture info (input from wincap, output for yolo)
    out_result, in_result = Pipe()  # Inference results (input from yolo, output for screen)
    self.running = True

    self.yolo = multiprocessing.Process(target=Yolo, args=(out_frame, in_result, model, img, source))
    self.wincap = multiprocessing.Process(target=WinCap, args=(in_frame, source, False, window))
    self.mouse = multiprocessing.Process(target=InterMouse, args=(out_mouse,))
    self.screen = multiprocessing.Process(target=Screen, args=(out_result, in_mouse, source, debug))

    self.wincap.start() # Will start capture instantly... model won't be ready
    self.mouse.start()
    self.screen.start()
    self.yolo.start()
    pass

  def run(self):
    print(f'[{self.name}] Starting...')

    while self.running:
      """ try:
        img = self.img_pipe.recv()
        if img.size > 0: print(f'Got Image!')
      except EOFError:
        break """
      if (not self.running): print(f'[{self.name}] Not Running')

    print(f'[{self.name}] End.')

  def exit_yolo(self):
    print(f'[{self.name}] Stopping...')
    self.mouse.terminate()
    self.screen.terminate()
    self.yolo.terminate()
    self.wincap.terminate()
    # Stop main program
    self.running = False

def parse_opt():
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', type=str, default='models/bestv2.pt', help='path to model.pt')
  parser.add_argument('--img', '--img-size', type=int, default=240, help='inference size (pixels)') #640
  parser.add_argument('--source', '--source-size', type=int, default=460, help='capture size (pixels)') #640
  parser.add_argument('--window', type=str, default=None, help='window name to capture')
  parser.add_argument('--debug', type=bool, default=False, help='Render inference results')
  opt = parser.parse_args()
  return opt

def main(opt):
  print('Detected params: ' + ', '.join(f'{k}={v}' for k, v in vars(opt).items()))
  a = MultiYOLO(**vars(opt))
  a.run()

if __name__ == "__main__":
  opt = parse_opt()
  main(opt)