import drivers.datahandler as data

def dummyGamma():
    if data.globalSetup["colourMode"] != 1:
        gamLength = 256+256+256
    else:
        if data.globalSetup["colourBiasHC"] == 3:
            gamLength = 32+32+32
        else:
            gamLength = 32+64+32
    for i in range(gamLength):
        data.gammaData.append(0)
    print("Dummy Gamma Length: ",gamLength)


def dummyPalette():
    if data.globalSetup["paletteSize"]>0:
        for i in range((data.globalSetup["paletteSize"]+1)*3):
            data.paletteData.append(0)
        print("Dummy Palette Length: ",(data.globalSetup["paletteSize"]+1)*3)
        print("Dummy Palette Size: ",(data.globalSetup["paletteSize"]+1))