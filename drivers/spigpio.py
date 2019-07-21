import RPi.GPIO as GPIO
import spidev
import time

spi = spidev.SpiDev()
params = [15600000,0, 8]
mcuState = "T"

PWR_ACTIVE = 15
FAN_ACTIVE = 7
MCU_RESET = 31
SIG_TO_MCU = 37
SIG_FROM_MCU = 40

C_RED = 18
C_BLUE = 11
C_GREEN = 13


    
def initialise():    
    GPIO.setmode(GPIO.BOARD)
    GPIO.cleanup()

    
    spi.open(0,0)
    spi.max_speed_hz = 10000000
    spi.mode = 0b10
    #NOTE WE USE CPOL HIGH DUE TO FAILSAFE RS485 LEVEL AND TO KEEP THINGS CONSTANT
    spi.bits_per_word = 8

    GPIO.setup(C_RED, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(C_GREEN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(C_BLUE, GPIO.OUT, initial=GPIO.HIGH)

    GPIO.setup(PWR_ACTIVE, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FAN_ACTIVE, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(MCU_RESET,  GPIO.OUT, initial=GPIO.HIGH)

    GPIO.setup(SIG_TO_MCU, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(SIG_FROM_MCU, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    panelpower("off")
    fan("off")    
    led("off")
    #GPIO.add_event_detect(SIG_FROM_MCU, GPIO.RISING, callback = mcu_status, bouncetime=1)

def led(colour):
    GPIO.output(C_BLUE, GPIO.HIGH)
    GPIO.output(C_GREEN, GPIO.HIGH)
    GPIO.output(C_RED, GPIO.HIGH)
    if(colour=="red"):
        GPIO.output(C_RED, GPIO.LOW)
    elif(colour=="green"):
        GPIO.output(C_GREEN, GPIO.LOW)
    elif(colour=="blue"):
        GPIO.output(C_BLUE, GPIO.LOW)
    elif(colour=="blue"):
        GPIO.output(C_BLUE, GPIO.LOW)
    elif(colour=="yellow"):
        GPIO.output(C_GREEN, GPIO.LOW)
        GPIO.output(C_RED, GPIO.LOW)
    elif(colour=="magenta"):
        GPIO.output(C_RED, GPIO.LOW)
        GPIO.output(C_BLUE, GPIO.LOW)
    elif(colour=="white"):
        GPIO.output(C_RED, GPIO.LOW)
        GPIO.output(C_GREEN, GPIO.LOW)
        GPIO.output(C_BLUE, GPIO.LOW)
        
def panelpower(state):
    if(state=="off"):
        GPIO.output(PWR_ACTIVE, GPIO.LOW)
    elif(state=="on"):
        GPIO.output(PWR_ACTIVE, GPIO.HIGH)
        
def fan(state):
    if(state=="off"):
        GPIO.output(FAN_ACTIVE, GPIO.LOW)
    elif(state=="on"):
        GPIO.output(FAN_ACTIVE, GPIO.HIGH)
        
def resetmcu():
    GPIO.output(MCU_RESET, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(MCU_RESET, GPIO.HIGH)
    
def spi_txrx(dataArr):    
    dataResponse = spi.xfer2(dataArr, *params)
    return dataResponse
   
def ping_mcu():
    GPIO.output(SIG_TO_MCU, GPIO.HIGH)
    GPIO.output(SIG_TO_MCU, GPIO.LOW)

def halt_until_ready(label=""):
    #start_time = time.time()
    #displayed = False
    while GPIO.input(SIG_FROM_MCU)==False:
        led("red")
        #if(time.time() - start_time > 2 and displayed == False):
            #print(label + "stuck")
            #displayed = True
    led("off")
    #if(time.time() - start_time > 0.1):
        #print(label+". signal in: ",time.time() - start_time)
    
   
def deinit():
    GPIO.cleanup()
    spi.close()
    