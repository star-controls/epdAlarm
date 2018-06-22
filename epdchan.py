
from softioc import builder, alarm
import time

#EPD PVs
#builder.SetDeviceName('EPD')

class epdchan:
  #alarm limits, same for all instances
  class limits:
    imon_max = 4.
    rmon_min = 0.
    rmon_max = 5.
    temp_max = 45.
  #_____________________________________________________________________________
  def __init__(self, ew, pp, tile):
    #epd tile
    self.ew = ew
    self.pp = pp
    self.tile = tile
    #values from mqtt
    self.vslope = -1.
    self.vcomp = -1.
    self.imon = -1.
    self.rmon = -1.
    self.state = ""
    #PVs for the channel, PP start at 1
    if self.pp > 0:
      pvnam = "{0:1d}:".format(self.ew)
      pvnam += "{0:02d}:".format(self.pp)
      pvnam += "{0:02d}:".format(self.tile)
      self.pv_imon = builder.aIn(pvnam+"imon", PREC=2)
      self.pv_rmon = builder.aIn(pvnam+"rmon", PREC=1)
      self.pv_temp = builder.aIn(pvnam+"temp", PREC=1)
    #counters for beyond-limits occurences
    self.imon_max_cnt = 0
    self.rmon_min_cnt = 0
    self.rmon_max_cnt = 0
    self.temp_max_cnt = 0
  #_____________________________________________________________________________
  def pvput(self):
    #put values to PVs
    self.pv_imon.set(self.imon)
    self.pv_rmon.set(self.rmon)
    temp = self.vcomp/self.vslope+8.6
    self.pv_temp.set(temp)
    #evaluate alarm conditions
    #current alarm
    if self.state.find("ivscan") == -1 and self.imon > self.limits.imon_max:
      self.imon_max_cnt += 1
      if self.imon_max_cnt > 1:
        self.pv_imon.set_alarm(alarm.MAJOR_ALARM, alarm=alarm.HIHI_ALARM)
    else:
      self.imon_max_cnt = 0
    #voltage alarm
    if self.state.find("off") == -1:
      if self.rmon < self.limits.rmon_min:
        self.rmon_min_cnt += 1
        if self.rmon_min_cnt > 1:
          self.pv_rmon.set_alarm(alarm.MAJOR_ALARM, alarm=alarm.LOLO_ALARM)
      else:
        self.rmon_min_cnt = 0
      if self.rmon > self.limits.rmon_max:
        self.rmon_max_cnt += 1
        if self.rmon_max_cnt > 1:
          self.pv_rmon.set_alarm(alarm.MAJOR_ALARM, alarm=alarm.HIHI_ALARM)
      else:
        self.rmon_max_cnt = 0
    #temperature alarm
    if temp > self.limits.temp_max:
      self.temp_max_cnt += 1
      if self.temp_max_cnt > 1:
        self.pv_temp.set_alarm(alarm.MAJOR_ALARM, alarm=alarm.HIHI_ALARM)
    else:
      self.temp_max_cnt = 0
    #print self.state
    #introduce small delay to prevent 'callbackRequest: cbLow ring buffer full'
    time.sleep(1.e-5)

  #_____________________________________________________________________________
  def set_invalid(self):
    self.pv_imon.set_alarm(alarm.INVALID_ALARM, alarm=alarm.UDF_ALARM)
    self.pv_rmon.set_alarm(alarm.INVALID_ALARM, alarm=alarm.UDF_ALARM)
    self.pv_temp.set_alarm(alarm.INVALID_ALARM, alarm=alarm.UDF_ALARM)
    time.sleep(1.e-5)
