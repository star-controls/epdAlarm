
from epdchan import epdchan
import paho.mqtt.client as mqtt
from watchdog import watchdog
from softioc import builder
import time
import pandas as pd

#EPD PVs
builder.SetDeviceName('EPD')

#list of all EPD channels as 3-index list
npp = 12
ntile = 31
elist = []
#east/west loop
for ew in range(0,2):
  elist.append([])
  #PP loop
  for ipp in range(0,npp+1):
    elist[ew].append([])
    #tile loop
    for itile in range(ntile+1):
      #PP starts at 1, handled in epdchan constructor
      elist[ew][ipp].append( epdchan(ew, ipp, itile) )

#watchdog timer for 60 seconds
wdt = watchdog(60, elist)

#file holding alarm limit values
csvlim = "limits.csv"
lframe = pd.read_csv(csvlim)
#set initial alarm values
elist[0][0][0].limits.imon_max = lframe['imon_max'][0]
elist[0][0][0].limits.rmon_min = lframe['rmon_min'][0]
elist[0][0][0].limits.rmon_max = lframe['rmon_max'][0]
elist[0][0][0].limits.temp_max = lframe['temp_max'][0]

#functions to show alarm limits
#_____________________________________________________________________________
def get_imon_max():
  return elist[0][0][0].limits.imon_max

#_____________________________________________________________________________
def get_rmon_min():
  return elist[0][0][0].limits.rmon_min

#_____________________________________________________________________________
def get_rmon_max():
  return elist[0][0][0].limits.rmon_max

#_____________________________________________________________________________
def get_temp_max():
  return elist[0][0][0].limits.temp_max

#_____________________________________________________________________________
def put_limit(key, val):
  #put limit value to file
  lframe[key][0] = val
  lframe.to_csv(csvlim, index=False)

#PVs to set alarm limits
#_____________________________________________________________________________
def set_imon_max(val):
  elist[0][0][0].limits.imon_max = val
  put_limit('imon_max', val)

imon_max_pv = builder.aOut("imon_max", on_update=set_imon_max, initial_value=get_imon_max(), PREC=2)

#_____________________________________________________________________________
def set_rmon_min(val):
  elist[0][0][0].limits.rmon_min = val
  put_limit('rmon_min', val)

rmon_min_pv = builder.aOut("rmon_min", on_update=set_rmon_min, initial_value=get_rmon_min(), PREC=1)

#_____________________________________________________________________________
def set_rmon_max(val):
  elist[0][0][0].limits.rmon_max = val
  put_limit('rmon_max', val)

rmon_max_pv = builder.aOut("rmon_max", on_update=set_rmon_max, initial_value=get_rmon_max(), PREC=1)

#_____________________________________________________________________________
def set_temp_max(val):
  elist[0][0][0].limits.temp_max = val
  put_limit('temp_max', val)

temp_max_pv = builder.aOut("temp_max", on_update=set_temp_max, initial_value=get_temp_max(), PREC=1)

#_____________________________________________________________________________
def init_alarm_limits():
  #put initial values to alarm limits PVs
  #imon_max_pv.set(get_imon_max())
  #rmon_min_pv.set(get_rmon_min())
  #rmon_max_pv.set(get_rmon_max())
  #temp_max_pv.set(get_temp_max())
  pass


#functions for mqtt message

#_____________________________________________________________________________
def get_msg_id(msg, idnam):
  #get message id
  return ( msg[msg.find(idnam):] ).split('"')[2]

#_____________________________________________________________________________
def process_msg(msg):
  #parse the message, get the values, put them to EPD channel objects
  #check message validity
  if get_msg_id(msg, "dcs_id") != "epd_controller" or get_msg_id(msg, "dcs_uid") != "tonko":
    return
  wdt.reset()
  #message header
  hstart = msg.find("[", msg.find("dcs_header")) + 1
  hend = msg.find("]")
  hlist = msg[hstart:hend].split(",")
  id_ew = hlist.index('"fps_quad"')
  id_pp = hlist.index('"fps_layer"')
  id_tile = hlist.index('"fps_channel"')
  id_vslope = hlist.index('"vslope"')
  id_vcomp = hlist.index('"temp"')
  id_imon = hlist.index('"imon0"')
  id_rmon = hlist.index('"rmon0"')
  id_state = hlist.index('"state"')
  #get values table
  vstart = msg.find("{", msg.find("dcs_values")) + 1
  vend = msg.find("}", vstart)
  vtab = msg[vstart:vend].split("]")
  #table lines loop
  for i in range(len(vtab)):
    if vtab[i] == "":
      continue
    #list of values
    vlist = vtab[i][vtab[i].find("[")+1:].split(",")
    #EPD indices
    ew = int(vlist[id_ew])
    pp = int(vlist[id_pp])
    tile = int(vlist[id_tile])
    #print repr(ew), repr(pp), repr(tile)
    #voltage and current values
    epd = elist[ew][pp][tile]
    epd.vslope = float(vlist[id_vslope])
    epd.vcomp = float(vlist[id_vcomp])
    epd.imon = float(vlist[id_imon])
    epd.rmon = float(vlist[id_rmon])
    epd.state = str(vlist[id_state]).lower().strip('"')
    #print repr(epd.ew), repr(epd.pp), repr(epd.tile), repr(epd.vslope), repr(epd.vcomp), repr(epd.imon), repr(epd.rmon)
    #put values to PVs in EPD object
    epd.pvput()

#mqtt client functions

#_____________________________________________________________________________
def on_connect(client, userdata, flags, rc):
  # The callback for when the client receives a CONNACK response from the server.
  print("MQTT connected with result code "+str(rc))
  client.subscribe("dcs/set/Control/epd/epd_control_fee")

#_____________________________________________________________________________
def on_message(client, userdata, msg):
  # The callback for when a PUBLISH message is received from the server.
  process_msg(msg.payload)

#_____________________________________________________________________________
def read_mqtt():
  #initialize alarm limits PVs
  init_alarm_limits()
  #main mqtt loop
  client = mqtt.Client()
  client.on_connect = on_connect
  client.on_message = on_message
  client.connect("mq01.starp.bnl.gov")
  client.loop_start()
  wdt.start()

  #watchdog test, 10 sec timeout
  #time.sleep(10)
  #client.loop_stop()
  #print "alarm on 0, 1, 0"
  #elist[0][1][0].set_invalid()
  #time.sleep(20)
  #print "running again"
  #client.loop_start()















