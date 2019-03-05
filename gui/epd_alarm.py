#!/usr/bin/python

import npyscreen as npy
import epics

class pv_edit:
    #_____________________________________________________________________________
    def __init__(self, frame, name, pvnam, xpos=None, ypos=None):
        self.frame = frame
        self.box = frame.add(npy.BoxBasic, name=name, editable=False, width=36, height=6)
        if xpos is None:
            xpos = self.box.relx
        else:
            self.box.relx = xpos
        if ypos is None:
            ypos = self.box.rely
        else:
            self.box.rely = ypos
        self.val = frame.add(npy.TitleFixedText, name="Alarm limit:", relx=xpos+1, rely=ypos+2, max_width=25, editable=False)
        self.edit = frame.add(npy.TitleText, name="New value:", relx=xpos+1, rely=ypos+3, max_width=25)
        self.pv = epics.PV(pvnam, callback=self.on_update)
        self.edit.value = self.pv.get(as_string=True)
        self.set = frame.add(npy.ButtonPress, name="Apply", when_pressed_function=self.on_new_val, relx=xpos+25, rely=ypos+3)
        frame.nextrely = ypos + 7

    #_____________________________________________________________________________
    def on_new_val(self):
        try:
            self.pv.put(self.edit.value)
        except:
            return

    #_____________________________________________________________________________
    def on_update(self, value=None, **kws):
        self.val.value = str(value)
        self.frame.DISPLAY()

class gui(npy.NPSApp):
    #_____________________________________________________________________________
    def main(self):
        frame = npy.Form(name="EPD Alarm Limits in Slow Controls", lines=19, columns=80)

        imon = pv_edit(frame, "Imon high alarm", "EPD:imon_max")
        temp = pv_edit(frame, "Temp high alarm", "EPD:temp_max")
        rmon_min = pv_edit(frame, "Rmon low alarm", "EPD:rmon_min", 40, 2)
        rmon_max = pv_edit(frame, "Rmon high alarm", "EPD:rmon_max", 40)

        npy.blank_terminal()

        frame.edit()

#_____________________________________________________________________________
if __name__ == "__main__":

    gui = gui()
    gui.run()


