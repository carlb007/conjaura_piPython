#
import drivers.spigpio as io

panels = []
paletteData = []
gammaData = []

globalSetup = {
    "panelCount" : 0,
    "colourMode" : 0, #0 = TC, 1 = HC, 2 = PALETTE
    "colourBiasHC": 0, #0 = 565, 1 = 655, 2 = 556
    "paletteSize" : 0,
    "bamBitRate":0,
    "mode":"Startup",
    "dataSegments":0,
    "segmentSize":0,
    "lastSegmentSize":0
}

def calc_data_segments():
    pass

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
    elif(mode==0 or mode=="Palette"):
        globalSetup["colourMode"] = 2
        if(globalSetup["paletteSize"]==0):
            globalSetup["paletteSize"] = 255
        
def set_palette(size,data):
    globalSetup["paletteSize"] = size
    if(size % 8 == 0):       
        if(len(data)/3 == size):
            paletteData = data
        else:
            print("Invalid palette length")
    else:
        print("Invalid palette size")

def set_bam(rate):
    if(rate==8 or rate=="8bit"):
        globalSetup["bamBitRate"] = 3
    elif(rate==7 or rate=="7bit"):
        globalSetup["bamBitRate"] = 2
    elif(rate==6 or rate=="6bit"):
        globalSetup["bamBitRate"] = 1
    elif(rate==5 or rate=="5bit"):
        globalSetup["bamBitRate"] = 0

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
        self.bitData = []
        self.touchData = []
        self.peripheralData = []
        globalSetup["panelCount"] += 1
        panels.append(self)
        
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
        hBits1_1 = 0
        
        hBits3and4_1 = globalSetup["dataSegments"]
        
        hBits2_2 = globalSetup["segmentSize"]>>10
        byte3 = globalSetup["segmentSize"] & 255
        
        hBits2_4 = globalSetup["lastSegmentSize"]>>10
        byte5 = globalSetup["lastSegmentSize"] & 255
        
        
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
            hBits2_4 = configDataLen>>10
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
                hBits2_4 = (paletteLen>>8) & 63
                byte5 = paletteLen & 255
                print(hBits2_4)
                print(byte5)
            
        elif(submode=="gammaSetup"):
            hBits2_1 = 32
            gammaLen = 768
            if(globalSetup["colourMode"]==1):
                gammaLen = (32+64+32)*3
            hBits2_4 = gammaLen>>10
            byte5 = gammaLen & 255
            
    byte1 = hBits1_1 | hBits2_1 | hBits3and4_1
    byte2 = hBits1_2 | hBits2_2
    byte4 = hBits1_4 | hBits2_4
    
    header = [byte1,byte2,byte3,byte4,byte5]
    if(autoSend):
        io.spi_txrx(header)
    
    return header
        