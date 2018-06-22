
from threading import Timer

class watchdog():
  #_____________________________________________________________________________
  def __init__(self, timeout, elist):
    self.timeout = timeout
    self.elist = elist
    self.timer = Timer(self.timeout, self.handler)
  #_____________________________________________________________________________
  def start(self):
    self.timer.start()
  #_____________________________________________________________________________
  def reset(self):
    self.timer.cancel()
    self.timer = Timer(self.timeout, self.handler)
    self.timer.start()
  #_____________________________________________________________________________
  def handler(self):
    print "Timeout in watchdog"
    #set all EPD channels as invalid
    for ew in range(len(self.elist)):
      for ipp in range(len(self.elist[ew])):
        if ipp == 0: continue
        for itile in range(len(self.elist[ew][ipp])):
          self.elist[ew][ipp][itile].set_invalid()
