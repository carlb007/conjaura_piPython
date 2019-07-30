#
import drivers.spigpio as io
import time

MAX_SEG_SIZE = 10240#8192 #MCU HAS 16KB AVAILABLE. SET AT 50% FOR NOW UNTIL WE CAN REFINE

panels = []
paletteData = []
gammaData = []
configData = []
streamData = []
returnData =[]
segments =[]

def status_check(state):
    if(state==True):
        io.led("red")
        print(globalSetup["lastError"])
        raise SystemExit(0)
    
    
class panel():
    def __init__(self,w,h):
        self.ID = globalSetup["panelCount"] + 1
        self.width = w
        self.height = h
        self.orientation = 0 #UDLR
        self.scanLines = 0 #0=8, 1=16
        self.ledActive = True
        self.throttle = 0 #0=100%, 1=80%, 2= 60%, 3 = 40%
        self.touchEnabled = True
        self.touchChannels = 0 #0=w*h/4
        self.touchSensetivity = 1 #0=4Bit, 1=8Bit
        self.edgeActive = True
        self.edgeThrottle = 0 #0=100%, 1=50%
        self.edgeDensity = 0 #0=3 per 8, 1 = 6 per 8
        self.peripheralType = 0 #0= NONE
        self.peripheralSettings = 0 #TBD
        self.peripheralReturnSize = 0 #TBD
        self.dataLength = 0;
        self.bitData = []
        self.edgeData = []
        self.touchData = []
        self.peripheralData = []
        globalSetup["panelCount"] += 1
        if(self.touchChannels==0):
            self.touchChannelCount = int((self.width / 4) *(self.height / 4))
            
        panels.append(self)
    
    def disableEdgeLights(self):
        self.edgeActive = False

globalSetup = {
    "panelCount" : 0,
    "colourMode" : 0, #0 = TC, 1 = HC, 2 = PALETTE
    "colourBiasHC": 0, #0 = 565, 1 = 655, 2 = 556
    "paletteSize" : 0,
    "bamBitRate":0,
    "mode":"Startup",
    "dataSegments":0,
    "currentSegment":0,
    "currentSegmentSize":0,
    "lastSegStartPanel" : 0,
    "lastSegEndPanel" : 0,
    "lastError": "None",
    "halt": False
}

def calc_panel_data_sizes():
    if globalSetup["colourMode"]==0:
        pixelDataSize = 3
    elif globalSetup["colourMode"]==1:
        pixelDataSize = 2
    else:
        pixelDataSize = 1        
    for thisPanel in panels:
        thisDataSize = (thisPanel.width * thisPanel.height)*pixelDataSize
        thisEdgeSize = 0
        if thisPanel.edgeActive:
            if thisPanel.edgeDensity == 0: #3 per 8
                thisEdgeSize = (((thisPanel.width * 2) + (thisPanel.height *2)) / 8) * 3
            elif thisPanel.edgeDensity == 1: #6 per 8
                thisEdgeSize = (((thisPanel.width * 2) + (thisPanel.height *2)) / 8) * 6
        thisPanel.dataLength = int(thisDataSize + (thisEdgeSize*pixelDataSize))
        #print("Panel",thisPanel.dataLength)


def calc_data_segments():  
    segments.clear()
    lastPanel = 0
    startPanel = 0
    while lastPanel<globalSetup["panelCount"]:
        segmentSize = 0
        start = lastPanel
        for i in range(start,globalSetup["panelCount"]):
            #print(i)
            thisPanel = panels[i]
            if((segmentSize + thisPanel.dataLength)<=MAX_SEG_SIZE):
                lastPanel += 1
                segmentSize += thisPanel.dataLength
            else:
                break
        segments.append([startPanel,lastPanel-1,segmentSize,[]])
        #print("Seg",[startPanel,lastPanel-1,segmentSize,[]])
        startPanel = lastPanel
        #print(startPanel)
    globalSetup["dataSegments"] = len(segments)    
        

def create_segment_data(segment):
    data = []
    for i in range(segments[segment][0], segments[segment][1]+1):        
        thisPanel = panels[i]
        #print(i,thisPanel.dataLength,thisPanel.edgeData)
        data.append(thisPanel.bitData)
        data.append(thisPanel.edgeData)
    segments[segment][3] = [item for sublist in data for item in sublist]


def send_segment_lengths():
    data = []
    for i in range(globalSetup["dataSegments"]):
        data.append(segments[i][2]>>8 & 255)
        data.append(segments[i][2] & 255)    
    print(data)
    io.spi_txrx(data)
    
                
def set_colour_mode(mode,bias=0):
    if(mode==0 or mode=="TrueColour"):
        globalSetup["colourMode"] = 0
    elif(mode==1 or mode=="HighColour"):
        globalSetup["colourMode"] = 1
        if(bias==0 or bias=="Green"):
            globalSetup["colourBiasHC"] = 0
        elif(bias==1 or bias=="Red"):
            globalSetup["colourBiasHC"] = 1
        elif(bias==2 or bias=="Blue"):
            globalSetup["colourBiasHC"] = 2
        elif(bias==3 or bias=="Even"):
            globalSetup["colourBiasHC"] = 3
        else:
            globalSetup["lastError"] = "Invalid BIAS mode"
            globalSetup["halt"] = True
    elif(mode==0 or mode=="Palette"):
        globalSetup["colourMode"] = 2
        if(globalSetup["paletteSize"]==0):
            globalSetup["paletteSize"] = 255
    else:
        globalSetup["lastError"] = "Invalid palette mode"
        globalSetup["halt"] = True
    
    return globalSetup["halt"]
        
        
def set_palette(size,data=""):
    globalSetup["paletteSize"] = size
    if((size+1) % 8 == 0):       
        if data:
            if(len(data)/3 == (size+1)):
                paletteData = data
            else:                
                globalSetup["lastError"] = "Invalid palette length"
                globalSetup["halt"] = True                
    else:
        globalSetup["lastError"] = "Invalid palette size"
        globalSetup["halt"] = True                
    
    return globalSetup["halt"]


def set_bam(rate):
    if(rate==8 or rate=="8bit"):
        globalSetup["bamBitRate"] = 3
    elif(rate==7 or rate=="7bit"):
        globalSetup["bamBitRate"] = 2
    elif(rate==6 or rate=="6bit"):
        globalSetup["bamBitRate"] = 1
    elif(rate==5 or rate=="5bit"):
        globalSetup["bamBitRate"] = 0
    else:
        globalSetup["lastError"] = "Invalid BAM rate"
        globalSetup["halt"] = True
    
    return globalSetup["halt"]
       

def build_config():
    allowedWidths = [8,16,24,32]
    allowedHeights = [8,16,24,32]
    for thisPanel in panels:
        
        ###########BYTE1##########
        bits8_7 = 0
        bits6_5 = 0
        bits4_3 = 0
        bit2 = 0
        bit1 = 0
        if(thisPanel.width in allowedWidths):
            bits8_7 = int((thisPanel.width / 8)-1) << 6
        else:
            globalSetup["lastError"] = "Invalid panel width"
            globalSetup["halt"] = True              
        
        if(thisPanel.height in allowedWidths):
            bits6_5 = (int(thisPanel.height / 8)-1) << 4
        else:
            globalSetup["lastError"] = "Invalid panel height"
            globalSetup["halt"] = True     
        
        if(thisPanel.orientation < 4):
            bits4_3 = thisPanel.orientation << 2
        else:
            globalSetup["lastError"] = "Invalid panel orientation"
            globalSetup["halt"] = True
        
        if(thisPanel.scanLines < 2):
            bit2 = thisPanel.scanLines << 1
        else:
            globalSetup["lastError"] = "Invalid panel scanline setup"
            globalSetup["halt"] = True
                
        byte = bits8_7 | bits6_5 | bits4_3 | bit2 | bit1
        configData.append(byte)
        
        ###########BYTE2##########
        bit8= 0
        bits7_6 = 0
        bits5_1 = 0
        
        bit8 = thisPanel.ledActive << 7
        if(thisPanel.throttle < 4):
            bit7_6 = thisPanel.throttle << 5
        else:
            globalSetup["lastError"] = "Invalid panel throttle"
            globalSetup["halt"] = True
        
        byte = bit8 | bits7_6 | bits5_1
        configData.append(byte)
        
        
        ###########BYTE3##########
        bit8 = 0
        bits7_6 = 0
        bit5 = 0
        bit4 = 0
        bit3 = 0
        bits2_1 = 0
        
        bit8 = thisPanel.touchEnabled << 7
        if(thisPanel.touchChannels < 4):
            bit7_6 = thisPanel.touchChannels << 5
        else:
            globalSetup["lastError"] = "Invalid touch channel count"
            globalSetup["halt"] = True
        
        bit5 = thisPanel.touchSensetivity << 4
        bit4= thisPanel.edgeActive << 3
        bit3= thisPanel.edgeThrottle << 2
        
        if(thisPanel.edgeDensity < 4):
            bits2_1 = thisPanel.edgeDensity
        else:
            globalSetup["lastError"] = "Invalid edge density"
            globalSetup["halt"] = True
        
        byte = bit8 | bits7_6 | bit5 | bit4 | bit3 | bits2_1
        configData.append(byte)
        
        ###########BYTE4##########
        
        bits8_6 = 0
        bits5_4 = 0
        bits3_2 = 0
        bit1 = 0
        
        if(thisPanel.peripheralType < 8):
            bits8_6 = thisPanel.peripheralType << 5
        else:
            globalSetup["lastError"] = "Invalid peripheral selection"
            globalSetup["halt"] = True
        
        if(thisPanel.peripheralSettings < 4):
            bits5_4 = thisPanel.peripheralSettings << 3
        else:
            globalSetup["lastError"] = "Invalid peripheral setting"
            globalSetup["halt"] = True
        
        if(thisPanel.peripheralReturnSize < 4):
            bits3_2 = thisPanel.peripheralReturnSize << 1
        else:
            globalSetup["lastError"] = "Invalid peripheral return size"
            globalSetup["halt"] = True
            
        byte = bits8_6 | bits5_4 | bits3_2 | bit1
        configData.append(byte)
        
        
    return globalSetup["halt"]


def build_header(mode,submode,autoSend=False):
    hBits1_1 = 0
    hBits2_1 = 0
    hBits3and4_1 = 0    
    hBits1_2 = 0
    hBits2_2 = 0    
    byte3 = 0    
    hBits1_4 = 0
    hBits2_4 = 0    
    byte5 = 0
    
    if(mode=="data"):              
        hBits2_2 = globalSetup["dataSegments"]#len(segments)#globalSetup["currentSegment"]    
        
    elif(mode=="address"):
        hBits1_1 = 64
        if(submode=="request"):
            hBits2_1 = 0
        elif(submode=="reset"):
            hBits2_1 = 16
        elif(submode=="finish"):
            hBits2_1 = 32
            
    elif(mode=="config"):
        hBits1_1 = 128
        if(submode=="panelSetup"):
            hBits2_1 = 0
            byte3 = globalSetup["panelCount"]
            configDataLen = globalSetup["panelCount"]*4
            hBits2_4 = configDataLen>>8 & 63
            byte5 = configDataLen & 255
            
        elif(submode=="colourSetup"):
            hBits2_1 = 16
            if(globalSetup["colourMode"]==0):
                hBits3_1 = 0
            elif(globalSetup["colourMode"]==1):
                hBits3_1 = 4
            elif(globalSetup["colourMode"]==2):
                hBits3_1 = 8
                       
            hBits4_1 = globalSetup["colourBiasHC"]
            
            hBits3and4_1 = hBits3_1 | hBits4_1
            
            hBits2_2 = globalSetup["bamBitRate"]
            byte3 = globalSetup["paletteSize"]
            
            if(globalSetup["colourMode"]==2):
                paletteLen = (globalSetup["paletteSize"]+1)*3
                hBits2_4 = paletteLen>>8 & 63
                byte5 = paletteLen & 255                
            
        elif(submode=="gammaSetup"):
            hBits2_1 = 32
            gammaLen = 768
            if(globalSetup["colourMode"]==1):
                if globalSetup["colourBiasHC"]==3:
                    gammaLen = (32+32+32)
                else:
                    gammaLen = (32+64+32)            
            hBits2_4 = gammaLen>>8 & 63
            byte5 = gammaLen & 255
            
        else:
            globalSetup["lastError"] = "Invalid sub config mode"
            globalSetup["halt"] = True    
            
    else:
        globalSetup["lastError"] = "Invalid primary config mode"
        globalSetup["halt"] = True
            
    byte1 = hBits1_1 | hBits2_1 | hBits3and4_1
    byte2 = hBits1_2 | hBits2_2
    byte4 = hBits1_4 | hBits2_4
    
    header = [byte1,byte2,byte3,byte4,byte5]
    print(submode,[byte1,byte2,byte3,byte4,byte5])
    if(autoSend):
        status_check(globalSetup["halt"])
        io.spi_txrx(header)
    
    #if(mode=="data"):
    #    print([byte1,byte2,byte3,byte4,byte5])
    #if(submode=="panelSetup"):
    #   print([byte1,byte2,byte3,byte4,byte5])
    #    time.sleep(2000)
    
    return [byte1,byte2,byte3,byte4,byte5]
        