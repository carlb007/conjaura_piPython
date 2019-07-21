import drivers.spigpio as io
import drivers.datahandler as data
import drivers.colours as colour
import time

io.initialise() 
io.resetmcu()
io.halt_until_ready()
io.ping_mcu() #CLEAR RETURN SIG
print("Ready")
time.sleep(.1)


#######################
#ADD DATA PANELS
#######################
for i in range(34):
    data.panel(16,16)#.disableEdgeLights()
    #DUMMY DATA FEED FOR NOW
    data.panels[i].bitData = [0] * 768
    data.panels[i].edgeData = [1] * 72
    
data.status_check(data.build_config())


#######################
#SET BAM BITS
#######################
data.status_check(data.set_bam("6bit"))


#######################
#CONFIGURE COLOUR MODE
#######################
#data.set_colour_mode("HighColour","Green")
data.status_check(data.set_colour_mode("TrueColour",""))
#data.status_check(data.set_palette(0))
#SET DUMMY GAMMA AND PALETTE(if needed) DATA SO WE HAVE SOMETHING TO SEND FOR NOW
colour.dummyGamma()
colour.dummyPalette()


#######################
#SEND COLOUR MODE HEADER / DATA
#######################
print("start colour ping")
io.ping_mcu()#PUT INTO HEADER MODE
data.build_header("config","colourSetup",True)
io.halt_until_ready("Col Header")
io.ping_mcu() #CLEAR RETURN SIG
if data.globalSetup["paletteSize"]>0:    
    io.spi_txrx(data.paletteData)
    io.halt_until_ready("Col Data")    
    io.ping_mcu() #CLEAR RETURN SIG
    

#######################
#SEND GAMMA MODE HEADER / DATA
#######################
print("start gamma ping")
io.ping_mcu()
data.build_header("config","gammaSetup",True)
io.halt_until_ready("Gamma Header")
io.ping_mcu() #CLEAR RETURN SIG
io.spi_txrx(data.gammaData)
io.halt_until_ready("Gamma Data")
io.ping_mcu() #CLEAR RETURN SIG


#######################
#SEND PANEL CONFIG DATA
#######################
print("start conf ping")
io.ping_mcu()
data.build_header("config","panelSetup",True)
io.halt_until_ready("Conf Header")
io.ping_mcu() #CLEAR RETURN SIG
io.spi_txrx(data.configData)
io.halt_until_ready("Conf Data")
io.ping_mcu() #CLEAR RETURN SIG


#######################
#READY UP OUR DATA SIZES
#######################
print("start data")
data.globalSetup["mode"] = "RUN"
data.calc_panel_data_sizes()
data.calc_data_segments()


#######################
#DATA INIT ROUTINE
#######################
io.ping_mcu()
d = data.build_header("data","",True)
io.halt_until_ready("Data Header")
io.ping_mcu() #CLEAR RETURN SIG
data.send_segment_lengths()
io.halt_until_ready("Data Seg Lengths")
io.ping_mcu() #CLEAR RETURN SIG


#######################
#DATA STREAMING
#######################
start_time = time.time()
TallyBits = 0
segsToRun = 6000
segmentPacketsSent = 0
for y in range(segsToRun):    
    #CAPTURE SRC DATA AND INSERT IT INTO PANEL.BITDATA WHEN CURRENT SEGMENT IS SET TO 0 - IE: START OF NEW FRAME
    data.globalSetup["currentSegment"] = 0
    for thisSegment in range(data.globalSetup["dataSegments"]):        
        data.create_segment_data(thisSegment)
        segmentPacketsSent += 1            
        TallyBits += data.segments[thisSegment][2]        
        response = io.spi_txrx(data.segments[thisSegment][3])
                
        #####################################################
        #HANDLE RETURN DATA TOUCH POINTS AND PERIPHERAL DATA#
        #####################################################
        bytesHandled = 0
        for panel in range(data.segments[thisSegment][0],data.segments[thisSegment][1]+1):            
            thisPanel = data.panels[panel]
            thisPanel.touchData.clear()
            if thisPanel.touchEnabled:
                for channel in range(thisPanel.touchChannelCount):    
                    if thisPanel.touchSensetivity == 1:
                        thisPanel.touchData.append(response[bytesHandled])
                    else:
                        thisPanel.touchData.append(response[bytesHandled]>>4)
                        thisPanel.touchData.append(response[bytesHandled] & 15)
                        channel += 1                    
                    bytesHandled += 1
            if thisPanel.peripheralType:
                #HANDLE PERIPHERAL DATA - TO DO WHEN WEVE GOT THE REST WORKING!
                pass
        #####################################################
        #####################################################
        #####################################################
            
        io.halt_until_ready("Data Stream")
        io.ping_mcu() #CLEAR RETURN SIG                
        data.globalSetup["currentSegment"] += 1
        
        
    elapsed_time = time.time() - start_time
    if(elapsed_time > 1):
        print("Avg Throughput: ",TallyBits)        
        start_time = time.time()
        TallyBits = 0
        
print("Completed ",segmentPacketsSent," segments")
io.deinit()
