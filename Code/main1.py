from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
from time import sleep
import sys
from IR_RX import *

@asm_pio(set_init=(PIO.OUT_LOW,) * 4)
def prog():
    wrap_target()
    set(pins, 8) [31] # 8
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    
    set(pins, 4) [31] # 4
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    
    set(pins, 2) [31] # 2
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    
    set(pins, 1) [31] # 1
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    wrap()
    

sm = StateMachine(0, prog, freq=100000, set_base=Pin(2))
#4.6 seconds is a whole spin

sm.exec("set(pins,0)")

RedLed = Pin(28, Pin.OUT)
GreenLed = Pin(15,Pin.OUT)


def blinkLed(led):
    led.toggle()
    sleep(0.05)
    led.toggle()

def bigSpinStepperCCW():
        sm.active(1)
        sleep(0.5)
        sm.active(0)

        
def spinStepperCCW():
        sm.active(1)
        sleep(0.1)
        sm.active(0)

        
def smallSpinStepperCCW():
        sm.active(1)
        sleep(0.05)
        sm.active(0)


def halfSpinStepperCCW():
        print('half Spin')
        GreenLed.on()
        sm.active(1)
        sleep(2.295)
        sm.active(0)
        GreenLed.off()

def callback(data, addr, ctrl):
    print(data)
    last_data = data;
    if data > 0:
        if (data == 69):
            GreenLed.on()
            RedLed.on()
            smallSpinStepperCCW()
        elif  (data == 70):
            GreenLed.on()
            RedLed.on()
            spinStepperCCW()
        elif (data == 71):
            GreenLed.on()
            RedLed.on()
            bigSpinStepperCCW()
        else:
            GreenLed.off()
            RedLed.off()
            blinkLed(RedLed)
            halfSpinStepperCCW()

ir = NEC_16(Pin(0,Pin.IN), callback)


    


