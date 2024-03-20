from machine import SPI, Pin
from uc8151 import UC8151
import math, array, time, random

spi = SPI(0, baudrate=12000000, phase=0, polarity=0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
eink = UC8151(spi,cs=17,dc=20,rst=21,busy=26,speed=3,no_flickering=True,inverted=False)

# eink.set_handmade_lut()

def draw_clock_hand(fb,x,y,angle,length,fill=False):
    angle %= 360
    angle /= 360
    angle *= 3.14*2
    bx1 = int(math.sin(angle-(3.1415/2))*5)
    by1 = -int(math.cos(angle-(3.1415/2))*5)
    bx2 = int(math.sin(angle+(3.1415/2))*5)
    by2 = -int(math.cos(angle+(3.1415/2))*5)
    hx = int(math.sin(angle)*length)
    hy = -int(math.cos(angle)*length)
    fb.poly(x,y,array.array('h',[bx1,by1,bx2,by2,hx,hy]),1,fill)

cx = 128//2
cy = 296//2 + 296//4
angle = 0
tick = 0
while True:
    eink.fb.fill(0)
    draw_clock_hand(eink.fb,cx,cy,angle,60,False)
    draw_clock_hand(eink.fb,cx,cy,angle//3,30,True)
    eink.fb.fill_rect(0,0,128,148,1)
    eink.fb.text(f"no_flick:{eink.no_flickering}",0,0,0)

    rect_size = 30
    x,y = random.randrange(eink.width-rect_size), \
          random.randrange(eink.height-rect_size)
    eink.fb.fill_rect(x,y,30,30,1)
    eink.fb.rect(x,y,30,30,0)
    x,y = random.randrange(eink.width-rect_size), \
          random.randrange(eink.height-rect_size)
    eink.fb.fill_rect(x,y,30,30,0)
    eink.fb.rect(x,y,30,30,1)

    eink.update(blocking=True)
    angle += 9
    tick += 1
    # Switch between flickering / no flickering mode to show
    # the difference.
    if ((tick+1) % 10) == 0:
        eink.set_speed(eink.speed,no_flickering=not eink.no_flickering)
