import drivers.spigpio as io
import drivers.datahandler as data
import drivers.colours as colour
import time


io.initialise()
io.panelpower("on")
time.sleep(1)
io.panelpower("off")
time.sleep(1)
io.panelpower("on")
time.sleep(1)

io.resetmcu()
io.halt_until_ready()
time.sleep(.5)
io.ping_mcu() #CLEAR RETURN SIG
print("LOCAL MCU Ready")
time.sleep(.5)


#######################
#ADD DATA PANELS
#######################
for i in range(34):
    data.panel(16,16)#.disableEdgeLights()
    #DUMMY DATA FEED FOR NOW
    data.panels[i].bitData = [0] * 768
    data.panels[i].edgeData = [1] * 72
    if i>0:
        data.panels[i].touchEnabled = False
   
data.panel(8,16)#.disableEdgeLights()
#DUMMY DATA FEED FOR NOW
data.panels[34].bitData = [0] * 384
data.panels[34].edgeData = [1] * 54
data.panels[34].touchEnabled = False

print (len(data.panels))

data.status_check(data.build_config())


#######################
#SET BAM BITS
#######################
data.status_check(data.set_bam("8bit"))


#######################
#CONFIGURE COLOUR MODE
#######################
data.set_colour_mode("TrueColour","Green")
#data.status_check(data.set_colour_mode("Palette","Red"))
#data.status_check(data.set_palette(255))
#SET DUMMY GAMMA AND PALETTE(if needed) DATA SO WE HAVE SOMETHING TO SEND FOR NOW
colour.dummyGamma()
colour.dummyPalette()


#######################
#ENTER ADDRESS MODE (INIT VIA UI)
#######################
print("Enter Address Mode? y/n")
str=input()
if str=='y':
    print("start address mode")
    io.ping_mcu()#PUT INTO HEADER MODE
    data.build_header("address","request",True)
    while io.GPIO.input(io.SIG_FROM_MCU)==False:
        str=input()    
        if str=='q':
            print("End Address mode")
            io.ping_mcu() #CLEAR RETURN SIG
            time.sleep(.1)
            io.ping_mcu()#PUT INTO HEADER MODE
            data.build_header("address","finish",True)
            io.halt_until_ready("Address finish")
            io.ping_mcu() #CLEAR RETURN SIG
            print("Finish Address Command")
            break
        elif str=='r':
            print("Reset Address mode")
            io.ping_mcu() #CLEAR RETURN SIG
            time.sleep(.1)
            io.ping_mcu()#PUT INTO HEADER MODE
            data.build_header("address","reset",True)       
            print("Reset Address Command")
       
    

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
print(len(data.gammaData))
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

time.sleep(.1)
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
segsToRun = 300
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
        panelID = 0
        showTouch = False
        for panel in range(data.segments[thisSegment][0],data.segments[thisSegment][1]+1):            
            thisPanel = data.panels[panel]            
            if thisPanel.touchEnabled:
                thisPanel.touchData.clear()
                for channel in range(thisPanel.touchChannelCount):    
                    if thisPanel.touchSensetivity == 1:
                        val = response[bytesHandled]
                        if(val > 2):
                            showTouch = True
                        thisPanel.touchData.append(val)
                    else:
                        thisPanel.touchData.append(response[bytesHandled]>>4)
                        thisPanel.touchData.append(response[bytesHandled] & 15)
                        channel += 1                    
                    bytesHandled += 1
                if showTouch:
                    print(panelID,thisPanel.touchData)
            if thisPanel.peripheralType:
                #HANDLE PERIPHERAL DATA - TO DO WHEN WEVE GOT THE REST WORKING!
                pass
            panelID +=1
        
        #####################################################
        #####################################################
        #####################################################
                  
        io.halt_until_ready("Data Stream ")        
        io.ping_mcu() #CLEAR RETURN SIG        
        data.globalSetup["currentSegment"] += 1
                
elapsed_time = time.time() - start_time
print("Avg Throughput: ",int((TallyBits/elapsed_time)/1000),"KB per second")
print("Bytes: ",TallyBits," In",elapsed_time," seconds")    
print("Completed ",segmentPacketsSent," segments")
#io.panelpower("off")
#io.deinit()
