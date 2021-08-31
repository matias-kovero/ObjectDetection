from interception_py.interception import *
import threading

INTER_M_LEFT_DOWN = interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_LEFT_BUTTON_DOWN.value
INTER_M_LEFT_UP = interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_LEFT_BUTTON_UP.value
INTER_M_RIGHT_DOWN = interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_RIGHT_BUTTON_DOWN.value
INTER_M_RIGHT_UP = interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_RIGHT_BUTTON_UP.value
INTER_M_MOVE = interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_MOVE.value

# Slowdown amount for aim assist
X_CLOSE   = 1.75
X_MEDIUM  = 1.55
X_FAR     = 1.25
Y_CLOSE   = 1.5
Y_MEDIUM  = 1.25
Y_FAR     = 1.05

class InterMouse:
  """
  Using interception C to modify current mouse buffer.  
  Creates 2 threads for buffer listen & send.
  If your mouse stops working, something is wrong with the code in this class - kill this process to gain access to mouse again.
  """
  # properties
  name = 'InterMouse' # Name used for logging
  device = None       # Mouse that is hooked
  mstroke = None      # Buffer info from hooked mouse
  c = None            # Context
  pipe_mouse = None   # Pipe
  thr_listen = None   # Listen Thread
  thr_adjust = None   # Sending Thread
  active = False      # State to tamper mouse buffer

  # Polling specific
  orig_move = (0,0)   # Contains original move

  # Target specific - https://www.youtube.com/watch?v=luLX6gCbPyw
  target_x = 0        # Target X coordinate from center (0, 0)
  target_y = 0        # Target Y coordinate from center (0, 0)
  target_d = 0        # Target distance from screen center.
  target_size = (0,0) # Target size (width, height)
  target_last = (0,0) # Target last position (x, y)
  target_move = (0,0) # Target movement from last frame to current frame.

  # constructor
  def __init__(self, out_mouse):
    """
    :param out_mouse: pipe to get vector information of ideal mouse position.
    """
    print(f'[{self.name}] Process launched.')
    self.c = interception()
    # Hook mouse
    self.c.set_filter(interception.is_mouse, 
      INTER_M_MOVE | INTER_M_LEFT_DOWN | INTER_M_LEFT_UP | INTER_M_RIGHT_DOWN | INTER_M_RIGHT_UP)

    self.pipe_mouse = out_mouse
    self.running = True

    self.thr_adjust = threading.Thread(target=self.run)
    self.thr_listen = threading.Thread(target=self.listen)

    self.thr_adjust.start()
    self.thr_listen.start()
  
  def run(self):
    """
    Thread for sending mouse buffer information to the OS. This is an MITM between Mouse & OS.
    Keep the code lightweight, as gets called on every mouse poll, ex. 1000 times/sec.
    If possible - lower your mouse polling rate as high polling rates have bunch of (0,0) moves.
    If this process fails, your mouse movement won't register - aka. you can't move your mouse.
    Should handle exceptions better, now if fails - kill process or reboot :(
    """
    print(f'[{self.name}] Thread send launched.')
    while self.running:
      self.device = self.c.wait() # This is blocking - will fire on every mouse poll.
      self.mstroke = self.c.receive(self.device) # Get polled info, you need to send this or mouse won't respond.
      if type(self.mstroke) is mouse_stroke:
        # Save original movement
        self.orig_move = (self.mstroke.x, self.mstroke.y)
        # Check / Update program state
        self.check_status()

        if self.active:
          self.aim_track()
        else:
          self.aim_assist()

      self.c.send(self.device, self.mstroke) # Finally send buffer to OS.
    print(f'[{self.name}] Thread send ended.')

  def listen(self):
    """
    Thread for listening vectors from pipe that our ML Model gives.
    This will be fired max the speed our model is running, in my case ~ 30FPS, so much slower than our polling rate.
    Main function is just to save coords from pipe - some small calculations.
    """
    print(f'[{self.name}] Thread listen launched.')
    while self.running:
      try:
        data = self.pipe_mouse.recv() # Read data from pipe
        (move, size, dist) = data
        self.target_x = move[0]
        self.target_y = move[1]
        self.target_size = size
        self.target_d = dist

        self.check_target_move(*move)

        self.target_last = (move[0], move[1])
        # self.size = size # Save target size?
      except EOFError:
        print(f'[{self.name}] Thread listen PIPE ERROR.')
        self.cleanup() # Kill other thread as well
        break
    print(f'[{self.name}] Thread listen ended.')

  def cleanup(self):
    """
    Could be useless code, as Python should clean things when it kills processes.
    Still to be 100% sure, running this.
    """
    self.running = False
    #self.c._destroy_context() # It seems this leaves process hanging - not good. Maybe the context is destroyed automatically?
  
  def check_status(self):
    """
    Simple way to check if we want to alter mouse buffer.
    """
    if self.mstroke.state > 0:
      if self.mstroke.state == INTER_M_LEFT_DOWN: self.active = True
      elif self.mstroke.state == INTER_M_RIGHT_DOWN: self.active = True
      else: self.active = False
  
  def check_target_move(self, x, y):
    """
    Check how much target has moved from last frame.
    """
    if (self.target_last[0] != 0 or self.target_last[1] != 0) and (x != 0 or y != 0):
      self.target_move = (x - self.target_last[0], y - self.target_last[1])

  def aim_assist(self):
    """
    Have controller aim assist for KBM. Slows down when close to target.
    Scuffed calculations - needs cleaning.
    """
    # Checking is done in main loop, no need here anymore.
    #self.check_status()
    # Yeet out if not active
    #if self.active != True: return

    # No target, don't assist.
    if (self.target_d == 0 and self.target_x == 0): return

    # Slow down sections
    (w, h) = self.target_size
    h = h * 0.55 # Y axis slowdown only on 55% area

    # Basic 1D vector stuff - still might be scuffed with unnececary parts.
    # X axis
    if abs(self.target_x) < (w * 0.45):   # Inside 45% area
      self.mstroke.x = int(self.mstroke.x / X_CLOSE)
    elif abs(self.target_x) < (w * 0.75): # Inside 75% area
      self.mstroke.x = int(self.mstroke.x / X_MEDIUM)
    elif abs(self.target_x) < w:          # Inside area
      self.mstroke.x = int(self.mstroke.x / X_FAR)
    
    # Y axis
    if abs(self.target_y) < (h * 0.45):   # Inside 45% area
      self.mstroke.y = int(self.mstroke.y / Y_CLOSE)
    elif abs(self.target_y) < (h * 0.75): # Inside 75% area
      self.mstroke.y = int(self.mstroke.y / Y_MEDIUM)
    elif abs(self.target_y) < h:          # Inside area
      self.mstroke.y = int(self.mstroke.y / Y_FAR)
  
  def aim_track(self):
    """
    An more agressive tracking. 
    Will move mouse the amount the target has moved since last ML inference frame.

    Caution! This movement, isn't really human like, as it sudden linear movement - and is "easily" detected.
    Should use bezier and take account last mouse movement amounts to smooth everything. 
    This is on you to solve - I'm not going to give everything.
    """
    if (self.target_move[0] != 0 or self.target_move[1] != 0):
      # These are relative movement, but does not account sensitivity on axes, so ex /2 sens in Y.
      self.mstroke.x = int(self.target_move[0])
      self.mstroke.y = int(self.target_move[1] / 2)
      # Reset target move, so that we don't repeat out tracking.
      self.target_move = (0, 0)
      # For bezier / smooth. Calc max allowed move - stash remaining movement, and rinse repeat till target @ center.
      # Also you could just adjust current movement and not replace the movement.