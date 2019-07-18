import drivers.spigpio as io
import drivers.datahandler as data
import drivers.colours as colour
import time
io.initialise()
    
io.resetmcu()
io.mcu_wait()
io.ping_mcu()

#######################
#ADD DATA PANELS
#######################
data.panel(16,16)
data.panel(16,16)


#######################
#SET BAM BITS
#######################
data.set_bam("6bit")


#######################
#CONFIGURE COLOUR MODE
#######################
#data.set_colour_mode("HighColour","Green")
data.set_colour_mode("Palette","")
data.set_palette(255)
#SET DUMMY GAMMA AND PALETTE(if needed) DATA SO WE HAVE SOMETHING TO SEND FOR NOW
colour.dummyGamma()
colour.dummyPalette()


#######################
#SEND COLOUR MODE HEADER / DATA
#######################
d = data.build_header("config","colourSetup",True)
io.mcu_wait()
if data.globalSetup["paletteSize"]>0:    
    io.spi_txrx(data.paletteData)
    io.mcu_wait()    


#######################
#SEND GAMMA MODE HEADER / DATA
#######################
io.ping_mcu()
d = data.build_header("config","gammaSetup",True)
io.mcu_wait()
io.spi_txrx(data.gammaData)

print(data.globalSetup)

for i in range(500000):    
    io.led("yellow")    
    time.sleep(1)
    io.led("off")
    
io.deinit()
