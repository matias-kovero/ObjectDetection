import numpy as np
import win32gui, win32ui, win32con
from PIL import Image
from pathlib import Path
import time
# import keyboard

W = 640
H = 640

class WinCap:
  # properties
  w = 0
  h = 0
  hwnd = None
  cropped_x = 0
  cropped_y = 0
  offset_x = 0
  offset_y = 0
  img_input = None
  running = False

  # constructor
  def __init__(self, img_input, source, gather=False, window_name=None, show_names=False) -> None:
    # keyboard.add_hotkey(kill_switch, self.cleanup)
    print(f'[WinCap] Process launched.')
    self.img_input = img_input
    # find handle for win we want to cap. If no name given, cap entire screen
    if window_name is None:
      self.hwnd = win32gui.GetDesktopWindow()
    else:
      self.hwnd = win32gui.FindWindow(None, window_name)
      #self.hwnd = win32gui.FindWindow(window_name, None)
      if not self.hwnd:
        if show_names: self.list_win_names()
        raise Exception('Window not found: {}'.format(window_name))

    # get win size [left, top, right, bottom]
    window_rect = win32gui.GetWindowRect(self.hwnd)
    self.w = window_rect[2] - window_rect[0]
    self.h = window_rect[3] - window_rect[1]

    if self.w < source or self.h < source:
      raise Exception('Window is smaller than {0}x{1}!'.format(source, source))

    self.cropped_x = int(self.w / 2 - (source/2))
    self.cropped_y = int(self.h / 2 - (source/2))
    self.w = source
    self.h = source

    # set the cropped coordinates offset so we can translate ss
    # images into actual screen positions
    self.offset_x = window_rect[0] + self.cropped_x
    self.offset_y = window_rect[1] + self.cropped_y
    self.running = True

    if not gather: self.run()

  def run(self):
    """
    Wincap boosted from original 20FPS to +200FP.
    Happy about the fix - capture isn't an bottleneck anymore.
    """
    last_time = time.time()
    while self.running:
      # if time.time() - last_time > 5:
      try:
        img = self.get_ss()
        if self.img_input and self.img_input.writable:
          self.img_input.send(img)
      except BrokenPipeError:
        break
      # print(f'{1/(time.time() - last_time):.1f} FPS')
      last_time = time.time()
    print(f'[WinCap] Main Thread ended.')

  def cleanup(self):
    print(f'[WinCap] Cleanup')
    # self.img_input.close()
    self.running = False

  def get_ss(self):
    # get win image data
    wDC = win32gui.GetWindowDC(self.hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBmp = win32ui.CreateBitmap()
    dataBmp.CreateCompatibleBitmap(dcObj, self.w, self.h)
    cDC.SelectObject(dataBmp)
    cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

    # convert the raw data for opencv
    signedIntsArray = dataBmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (self.h, self.w, 4)

    # free resources
    dcObj.DeleteDC() 
    cDC.DeleteDC() 
    win32gui.ReleaseDC(self.hwnd, wDC)
    win32gui.DeleteObject(dataBmp.GetHandle())

    # drop alpha channel (optional) you will lose about 10 FPS
    # img = img[...,:3]

    # make image C_CONTIGUOUS to avoid errors
    # see the discussion here:
    # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
    # img = np.ascontiguousarray(img)

    return img

  def save_ss(self):
    """
    This code was used to gather images from the game. 
    These images where then used as an dataset to train our model.
    """
    # get win image data
    wDC = win32gui.GetWindowDC(self.hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBmp = win32ui.CreateBitmap()
    dataBmp.CreateCompatibleBitmap(dcObj, self.w, self.h)
    cDC.SelectObject(dataBmp)
    cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

    # save ss
    dataBmp.SaveBitmapFile(cDC, 'debug.bmp')
    # create images folder if not found
    Path('./images').mkdir(parents=True, exist_ok=True)
    Image.open('debug.bmp').save('images/{}.jpg'.format(int(time.time())))

    # free resources
    dcObj.DeleteDC()
    cDC.DeleteDC() 
    win32gui.ReleaseDC(self.hwnd, wDC)
    win32gui.DeleteObject(dataBmp.GetHandle())

  @staticmethod
  def list_win_names():
    """
    Find the name of the win you are intrested in
    """
    print('-- List of windows:')
    def winEnumHandler(hwnd, ctx):
      if win32gui.IsWindowVisible(hwnd):
        print(hex(hwnd), win32gui.GetWindowText(hwnd))
    # I already hate python indentation
    win32gui.EnumWindows(winEnumHandler, None)
    print('--')

  def get_screen_pos(self, pos):
    """
    Translate a pixel position on a ss image to a pixel position on screen
    This code is currently legacy, isn't used anymore. Might be still helpful for something?
    """
    return (pos[0] + self.offset_x, pos[1] + self.offset_y)