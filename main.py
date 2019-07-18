import drivers.spigpio as io
import drivers.datahandler as data
import time
io.initialise()

io.resetmcu()
io.mcu_wait()

data.panel(16,16)
data.panel(16,16)
data.set_colour_mode("Palette","Green")
data.set_bam("6bit")




print(data.globalSetup)

for i in range(500000):    
    io.led("red")
    io.panelpower("off")
    io.fan("off")
    data.build_header("config","colourSetup",True)
    time.sleep(1)
    io.led("off")    
    time.sleep(5)
    
io.deinit()
