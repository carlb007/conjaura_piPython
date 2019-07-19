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
for i in range(32):
    data.panel(16,16).disableEdgeLights()
    data.panels[i].bitData = [1,2,3,4,5]
    
data.status_check(data.build_config())


#######################
#SET BAM BITS
#######################
data.status_check(data.set_bam("6bit"))


#######################
#CONFIGURE COLOUR MODE
#######################
#data.set_colour_mode("HighColour","Green")
data.status_check(data.set_colour_mode("Palette",""))
data.status_check(data.set_palette(255))
#SET DUMMY GAMMA AND PALETTE(if needed) DATA SO WE HAVE SOMETHING TO SEND FOR NOW
colour.dummyGamma()
colour.dummyPalette()


#######################
#SEND COLOUR MODE HEADER / DATA
#######################
data.build_header("config","colourSetup",True)
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
io.mcu_wait()


#######################
#SEND PANEL CONFIG DATA
#######################
io.ping_mcu()
d = data.build_header("config","panelSetup",True)
io.mcu_wait()
io.spi_txrx(data.configData)
io.mcu_wait()


#######################
#READY UP OUR DATA SIZES
#######################
data.calc_panel_data_sizes()
data.calc_segment_count()
data.globalSetup["mode"] = "RUN"


#######################
#DATA ROUTINE
#######################
while data.globalSetup["mode"]=="RUN":
    data.segment_retstart()
    for thisSegment in range(0,data.globalSetup["dataSegments"]):    
        data.calc_data_segment()
        #FETCH PIXEL DATA FROM SRC AND INSERT INTO PANEL.BITDATA HOLDERS- FROM PYGAME OR OTHER SRC
        data.build_header("data","",True)
        io.mcu_wait()
        io.led("yellow")        
        data.returnData = io.spi_txrx([item for sublist in data.streamData for item in sublist])        
        io.mcu_wait()
        io.led("off")
    time.sleep(1)

io.deinit()
