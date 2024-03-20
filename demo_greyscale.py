from machine import SPI,Pin
from uc8151 import UC8151
import random

spi = SPI(0, baudrate=12000000, phase=0, polarity=0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
eink = UC8151(spi,cs=17,dc=20,rst=21,busy=26,speed=2,no_flickering=False)

for greyscale in [4,8,16,32]:
    eink.load_greyscale_image("dama.grey",greyscale)
