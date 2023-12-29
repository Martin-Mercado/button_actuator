from machine import Pin
from machine import Timer
from array import array
from utime import ticks_us
from utime import ticks_diff
from rp2 import PIO, StateMachine, asm_pio
from time import sleep
import sys
import _thread


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

class IR_RX():
    # Result/error codes
    # Repeat button code
    REPEAT = -1
    # Error codes
    BADSTART = -2
    BADBLOCK = -3
    BADREP = -4
    OVERRUN = -5
    BADDATA = -6
    BADADDR = -7

    def __init__(self, pin, nedges, tblock, callback, *args):  # Optional args for callback
        self._pin = pin
        self._nedges = nedges
        self._tblock = tblock
        self.callback = callback
        self.args = args
        self._errf = lambda _ : None
        self.verbose = False

        self._times = array('i',  (0 for _ in range(nedges + 1)))  # +1 for overrun
        pin.irq(handler = self._cb_pin, trigger = (Pin.IRQ_FALLING | Pin.IRQ_RISING))
        self.edge = 0
        self.tim = Timer(-1)  # Sofware timer
        self.cb = self.decode

    # Pin interrupt. Save time of each edge for later decode.
    def _cb_pin(self, line):
        t = ticks_us()
        # On overrun ignore pulses until software timer times out
        if self.edge <= self._nedges:  # Allow 1 extra pulse to record overrun
            if not self.edge:  # First edge received
                self.tim.init(period=self._tblock , mode=Timer.ONE_SHOT, callback=self.cb)
            self._times[self.edge] = t
            self.edge += 1

    def do_callback(self, cmd, addr, ext, thresh=0):
        self.edge = 0
        if cmd >= thresh:
            self.callback(cmd, addr, ext, *self.args)
        else:
            self._errf(cmd)

    def error_function(self, func):
        self._errf = func

    def close(self):
        self._pin.irq(handler = None)
        self.tim.deinit()


class NEC_ABC(IR_RX):
    def __init__(self, pin, extended, callback, *args):
        # Block lasts <= 80ms (extended mode) and has 68 edges
        super().__init__(pin, 68, 80, callback, *args)
        self._extended = extended
        self._addr = 0

    def decode(self, _):
        try:
            if self.edge > 68:
                raise RuntimeError(self.OVERRUN)
            width = ticks_diff(self._times[1], self._times[0])
            if width < 4000:  # 9ms leading mark for all valid data
                raise RuntimeError(self.BADSTART)
            width = ticks_diff(self._times[2], self._times[1])
            if width > 3000:  # 4.5ms space for normal data
                if self.edge < 68:  # Haven't received the correct number of edges
                    raise RuntimeError(self.BADBLOCK)
                # Time spaces only (marks are always 562.5µs)
                # Space is 1.6875ms (1) or 562.5µs (0)
                # Skip last bit which is always 1
                val = 0
                for edge in range(3, 68 - 2, 2):
                    val >>= 1
                    if ticks_diff(self._times[edge + 1], self._times[edge]) > 1120:
                        val |= 0x80000000
            elif width > 1700: # 2.5ms space for a repeat code. Should have exactly 4 edges.
                raise RuntimeError(self.REPEAT if self.edge == 4 else self.BADREP)  # Treat REPEAT as error.
            else:
                raise RuntimeError(self.BADSTART)
            addr = val & 0xff  # 8 bit addr
            cmd = (val >> 16) & 0xff
            if cmd != (val >> 24) ^ 0xff:
                raise RuntimeError(self.BADDATA)
            if addr != ((val >> 8) ^ 0xff) & 0xff:  # 8 bit addr doesn't match check
                if not self._extended:
                    raise RuntimeError(self.BADADDR)
                addr |= val & 0xff00  # pass assumed 16 bit address to callback
            self._addr = addr
        except RuntimeError as e:
            cmd = e.args[0]
            addr = self._addr if cmd == self.REPEAT else 0  # REPEAT uses last address
        # Set up for new data burst and run user callback
        self.do_callback(cmd, addr, 0, self.REPEAT)

class NEC_16(NEC_ABC):
    def __init__(self, pin, callback, *args):
        super().__init__(pin, True, callback, *args)


def blinkLed(led):
    led.toggle()
    sleep(0.05)
    led.toggle()

stepperActive = False

def halfSpinStepper():
        GreenLed.toggle()
        global stepperActive
        stepperActive = True
        sm.active(1)
        sleep(2.3)
        sm.active(0)
        stepperActive = False
        GreenLed.toggle()


def callback(data, addr, ctrl):
    global stepperActive
    
    if data > 0:
        if not stepperActive:
            _thread.start_new_thread(halfSpinStepper,())
        blinkLed(RedLed)
        

        
ir = NEC_16(Pin(0,Pin.IN), callback)


    

