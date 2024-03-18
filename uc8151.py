# MicroPython driver for the UC8151 /IL0373 e-paper display.
# This is the e-paper type used in the Badger 2040.
#
# Copyright(C) 2024 Salvatore Sanfilippo <antirez@gmail.com>
# MIT license.

from machine import Pin
import time, framebuf

### Commands list.
# Commands are executed putting the DC line in command mode
# and sending the command as first byte, followed if needed by
# the data arguments (but with DC in data mode).

CMD_PSR      = const(0x00)
CMD_PWR      = const(0x01)
CMD_POF      = const(0x02)
CMD_PFS      = const(0x03)
CMD_PON      = const(0x04)
CMD_PMES     = const(0x05)
CMD_BTST     = const(0x06)
CMD_DSLP     = const(0x07)
CMD_DTM1     = const(0x10)
CMD_DSP      = const(0x11)
CMD_DRF      = const(0x12)
CMD_DTM2     = const(0x13)
CMD_LUT_VCOM = const(0x20)
CMD_LUT_WW   = const(0x21)
CMD_LUT_BW   = const(0x22)
CMD_LUT_WB   = const(0x23)
CMD_LUT_BB   = const(0x24)
CMD_PLL      = const(0x30)
CMD_TSC      = const(0x40)
CMD_TSE      = const(0x41)
CMD_TSR      = const(0x43)
CMD_TSW      = const(0x42)
CMD_CDI      = const(0x50)
CMD_LPD      = const(0x51)
CMD_TCON     = const(0x60)
CMD_TRES     = const(0x61)
CMD_REV      = const(0x70)
CMD_FLG      = const(0x71)
CMD_AMV      = const(0x80)
CMD_VV       = const(0x81)
CMD_VDCS     = const(0x82)
CMD_PTL      = const(0x90)
CMD_PTIN     = const(0x91)
CMD_PTOU     = const(0x92)
CMD_PGM      = const(0xa0)
CMD_APG      = const(0xa1)
CMD_ROTP     = const(0xa2)
CMD_CCSET    = const(0xe0)
CMD_PWS      = const(0xe3)
CMD_TSSET    = const(0xe5)

### Register values

# PSR
RES_96x230   = const(0b00000000)
RES_96x252   = const(0b01000000)
RES_128x296  = const(0b10000000)
RES_160x296  = const(0b11000000)
LUT_OTP      = const(0b00000000)
LUT_REG      = const(0b00100000)
FORMAT_BWR   = const(0b00000000)
FORMAT_BW    = const(0b00010000)
SCAN_DOWN    = const(0b00000000)
SCAN_UP      = const(0b00001000)
SHIFT_LEFT   = const(0b00000000)
SHIFT_RIGHT  = const(0b00000100)
BOOSTER_OFF  = const(0b00000000)
BOOSTER_ON   = const(0b00000010)
RESET_SOFT   = const(0b00000000)
RESET_NONE   = const(0b00000001)

# PWR
VDS_EXTERNAL = const(0b00000000)
VDS_INTERNAL = const(0b00000010)
VDG_EXTERNAL = const(0b00000000)
VDG_INTERNAL = const(0b00000001)
VCOM_VD      = const(0b00000000)
VCOM_VG      = const(0b00000100)
VGHL_16V     = const(0b00000000)
VGHL_15V     = const(0b00000001)
VGHL_14V     = const(0b00000010)
VGHL_13V     = const(0b00000011)

# BOOSTER
START_10MS = const(0b00000000)
START_20MS = const(0b01000000)
START_30MS = const(0b10000000)
START_40MS = const(0b11000000)
STRENGTH_1 = const(0b00000000)
STRENGTH_2 = const(0b00001000)
STRENGTH_3 = const(0b00010000)
STRENGTH_4 = const(0b00011000)
STRENGTH_5 = const(0b00100000)
STRENGTH_6 = const(0b00101000)
STRENGTH_7 = const(0b00110000)
STRENGTH_8 = const(0b00111000)
OFF_0_27US = const(0b00000000)
OFF_0_34US = const(0b00000001)
OFF_0_40US = const(0b00000010)
OFF_0_54US = const(0b00000011)
OFF_0_80US = const(0b00000100)
OFF_1_54US = const(0b00000101)
OFF_3_34US = const(0b00000110)
OFF_6_58US = const(0b00000111)

# PFS
FRAMES_1   = const(0b00000000)
FRAMES_2   = const(0b00010000)
FRAMES_3   = const(0b00100000)
FRAMES_4   = const(0b00110000)

# TSE
TEMP_INTERNAL = const(0b00000000)
TEMP_EXTERNAL = const(0b10000000)
OFFSET_0      = const(0b00000000)
OFFSET_1      = const(0b00000001)
OFFSET_2      = const(0b00000010)
OFFSET_3      = const(0b00000011)
OFFSET_4      = const(0b00000100)
OFFSET_5      = const(0b00000101)
OFFSET_6      = const(0b00000110)
OFFSET_7      = const(0b00000111)
OFFSET_MIN_8  = const(0b00001000)
OFFSET_MIN_7  = const(0b00001001)
OFFSET_MIN_6  = const(0b00001010)
OFFSET_MIN_5  = const(0b00001011)
OFFSET_MIN_4  = const(0b00001100)
OFFSET_MIN_3  = const(0b00001101)
OFFSET_MIN_2  = const(0b00001110)
OFFSET_MIN_1  = const(0b00001111)

# PLL flags
HZ_29      = const(0b00111111)
HZ_33      = const(0b00111110)
HZ_40      = const(0b00111101)
HZ_50      = const(0b00111100)
HZ_67      = const(0b00111011)
HZ_100     = const(0b00111010)
HZ_200     = const(0b00111001)

class UC8151:
    def __init__(self,spi,*,cs,dc,rst,busy,width=128,height=296,speed=0,mirror_x=False,mirror_y=False,inverted=False,no_flickering=False,debug=False,full_update_period=50):
        self.spi = spi
        self.cs = Pin(cs,Pin.OUT) if cs != None else None
        self.dc = Pin(dc,Pin.OUT) if dc != None else None
        self.rst = Pin(rst,Pin.OUT) if rst != None else None
        self.busy = Pin(busy,Pin.IN) if busy != None else None
        self.width = width
        self.height = height
        self.speed = speed
        self.no_flickering = no_flickering
        self.inverted = inverted
        self.mirror_x = mirror_x
        self.mirror_y = mirror_y
        self.debug = debug
        self.initialize_display()
        self.raw_fb = bytearray(width*height//8)
        self.fb = framebuf.FrameBuffer(self.raw_fb,width,height,framebuf.MONO_HLSB)

        # Updates done with the current speed settings.
        self.update_count = 0

        # From time to time, if partial updates or no-flickering updates
        # are used, we perform a full update regardless, to remove ghosting,
        # make the background color more even and so forth.
        self.full_update_period = full_update_period

    # Return true if the display is busy performing an update, or also
    # if for any other reason it is not able to accept commands right now.
    def is_busy(self):
        return self.busy.value() == False # Low on busy condition.

    def wait_ready(self):
        if self.busy == None: return
        while self.is_busy(): pass

    # Perform hardware reset.
    def reset(self):
        self.rst.off()
        time.sleep_ms(10)
        self.rst.on()
        time.sleep_ms(10)
        self.wait_ready()

    # Send just a command, just data, or a command + data, depending
    # on cmd or data being both bytes() / bytearrays() or None.
    def write(self,cmd=None,data=None):
        self.wait_ready()
        self.cs.off()
        self.dc.off() # Command mode
        self.spi.write(bytes([cmd]))
        if data:
            if isinstance(data,int): data = bytes([data])
            if isinstance(data,list): data = bytes(data)
            self.dc.on() # Data mode
            self.spi.write(data)
        self.cs.on()

    # This function sets the PSR register, a key register to
    # set up the panel configuration. We call this function each
    # time a new speed / LUTs are configured, because when we
    # revert to the default LUTs (speed 0) the PSR register
    # must be set to look into the internal tables.
    def set_panel_configuration(self):
        # Panel configuration: resolution, format and so forth.
        psr_settings = FORMAT_BW | BOOSTER_ON | RESET_NONE

        if self.width == 96 and self.height == 230:
            psr_settings |= RES_96x230
        elif self.width == 96 and self.height == 252:
            psr_settings |= RES_96x252
        elif self.width == 128 and self.height == 296:
            psr_settings |= RES_128x296
        elif self.width == 160 and self.height == 296:
            psr_settings |= RES_160x296
        else:
            raise ValueError("Unsupported display resolution specified")

        # If we select the default update speed, we will use the
        # lookup tables defined by the device. Otherwise the values for
        # the lookup tables must be read from the registers we set.
        if self.speed == 0:
            psr_settings |= LUT_OTP
        else:
            psr_settings |= LUT_REG

        # Configure mirroring.
        psr_settings |= SHIFT_LEFT if self.mirror_x else SHIFT_RIGHT
        psr_settings |= SCAN_DOWN if self.mirror_y else SCAN_UP

        self.write(CMD_PSR,psr_settings)

    def initialize_display(self):
        self.reset()

        # Soft reset
        self.write(CMD_PSR,RESET_SOFT)
        self.wait_ready()

        # Setup the pain manel configuration
        self.set_panel_configuration()

        # Set the lookup tables depending on the speed.
        self.set_waveform_lut()

        # Here we set the voltage levels that are used for the low-high
        # transitions states, driven by the waveforms provided in the
        # lookup tables for refresh.
        #
        # The VCOM_DC is left to the default of -0.10v, since
        # CMD_VDCS is not given.
        #
        # VDH/VDL are set to what is the chip default: 10v.
        # There are drivers around using 11v, but I guess given that
        # everything seems fine with 10v, there is no reason to increase
        # voltage and current at the risk of damage.
        self.write(CMD_PWR, \
            [VDS_INTERNAL|VDG_INTERNAL,
             VCOM_VD|VGHL_16V, # VCOM_VD sets VCOM voltage to VD[HL]+VCOM_DC
             0b100110, # +10v VDH
             0b100110, # -10v VDL
             0b000011  # VDHR default (For red pixels, not used here)
             ])
        self.write(CMD_PON)
        self.wait_ready()

        # Booster soft start configuration.
        self.write(CMD_BTST, \
            [START_10MS | STRENGTH_3 | OFF_6_58US,
             START_10MS | STRENGTH_3 | OFF_6_58US,
             START_10MS | STRENGTH_3 | OFF_6_58US])

        # Setup the duration (in frames) for the discharge executed for
        # power-off. This is useful to left the pixels in a "stable"
        # configuration. One frame means 10 milliseconds at 100 HZ.
        self.write(CMD_PFS,FRAMES_1)

        # Use the internal temperature sensor. Unfortunately there is
        # no input line connected, so we can't read the temperature.
        self.write(CMD_TSE,TEMP_INTERNAL | OFFSET_0)

        # Set non overlapping period for Gate and Source lines.
        # TCON set to 0x22 means 12 periods (1 period is 660ns) for
        # both S->G and G->S transition.
        self.write(CMD_TCON,0x22)

        # VCOM data and interval settings. We can use this register in order
        # to invert the display so that black is white and white is black,
        # without resorting to software changes.
        #
        # The bits 7:6 are the "border data selection":
        # For black/white mode: 00,11 = floating. 01: LUTBW, 10: LUTWB.
        # For black/white/red: 00 floating, 01 LUTR, 10 LUTW, 11 LUTB.
        # We keep it at 11 since it is floating in all the cases so
        # that the border will not flicker.
        self.write(CMD_CDI,0b11_01_1100 if self.inverted else 0b11_00_1100)

        # PLL clock frequency. Setting it to 100 HZ means that each
        # "frame" in the counts in the refresh waveforms lookup tables will
        # last 10 milliseconds. Certain drivers set it to 200 HZ for the fast
        # modes, but in my tests it does not work well at all, so we take
        # it to a fixed 100 HZ.
        self.write(CMD_PLL,HZ_100)

        # Power off the display. We will pover on it again on the
        # next update of the image.
        self.write(CMD_POF)
        self.wait_ready()

    # This function is only for debugging. We use computed LUTs, however
    # it is quite handy in order to experiment with different display
    # capabilities to play with the tables by hand and quickly check the
    # results. This function should be removed eventually since it uses
    # a lot of MicroPython memory because of the tables.
    #
    # P.S. the currently set LUTs in the tables are just trivial
    # examples and don't have any special use.
    def set_handmade_lut(self):
        VCOM = bytes([
          0x00, 0x01, 0x01, 0x02, 0x00, 0x01,
          0x00, 0x02, 0x02, 0x03, 0x00, 0x02,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00
        ])
        BW = bytes([
          0x99, 0x02, 0x02, 0x00, 0x00, 0x01,
          0xaa, 0x02, 0x02, 0x03, 0x00, 0x02,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        WB = bytes([
          0x66, 0x02, 0x02, 0x00, 0x00, 0x01,
          0x55, 0x02, 0x02, 0x03, 0x00, 0x02,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        WW = bytes([
          0xaa, 0x01, 0x01, 0x01, 0x01, 0x01,
          0xaa, 0x02, 0x02, 0x03, 0x00, 0x02,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        BB = bytes([
          0x55, 0x01, 0x01, 0x01, 0x01, 0x01,
          0x55, 0x02, 0x02, 0x03, 0x00, 0x02,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
          0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        self.write(CMD_LUT_VCOM,VCOM)
        self.write(CMD_LUT_BW,BW)
        self.write(CMD_LUT_WB,WB)
        self.write(CMD_LUT_BB,BB)
        self.write(CMD_LUT_WW,WW)

    # This function (after all this big comment) sets the lookup tables
    # used during the display refresh. Before reading it, it's a good
    # idea to understand how LUTs are encoded:
    #
    # We have a table for each transition possibile:
    # white -> white (WW)
    # white -> black (WB)
    # black -> black (BB)
    # black -> white (BW)
    # and a final table that controls the VCOM common voltage.
    #
    # The update process happens in steps, each 7 rows of each
    # table tells the display how to set each pixel based on the
    # transition (WW, WB, BB, BW) and VCOM in each step. Usually just
    # three or two steps are used.
    #
    # When we talk about a "WW" transition or "WB" transition, what we
    # mean is the difference between the pixel value set in the *last*
    # display update, and the pixel value of the *current* display update.
    # So if in the previous update a pixel was white, and later the pixel
    # turns black, then it's a WB transition and will be handled by the
    # WB LUT.
    #
    # VCOM table is different and explained later, but for the first four
    # tables, this is how to interpret them. For instance the
    # lookup for WW in the second row (step 1) could be set to:
    #
    # 0x60, 0x02, 0x02, 0x00, 0x00, 0x01 -> last byte = repeat count
    #  \     |      |    |     |
    #   \    +------+----+-----+-> number of frames
    #    \_ four transitions
    #
    # The first byte must be read as four two bits integers:
    #
    # 0x60 is: 01|10|00|00
    #
    # Where each 2 bit number menas:
    # 00 - Put to ground
    # 01 - Put to VDH voltage (10v in our config): pixel becomes black
    # 10 - Put to VDL voltage (-10v in our config): pixel becomes white
    # 11 - Floating / Not used.
    #
    # Then the next four bytes in the row mean how many
    # "frames" we hold a given state (the frame duration depends on the
    # frequency set in the PLL, here we configure it to 100 HZ so 10ms).
    # 
    # So in the above case: hold pixel at VDH for 2 frames, then
    # hold at VDL for 2 frame. The last two entries say 0 frames,
    # so they are not used. The final byte in the row, 0x01, means
    # that this sequence must be repeated just once. If it was 2
    # the whole sequence would repeat 2 times and so forth.
    #
    # The VCOM table is similar, but the bits meaning is different:
    # 00 - Put VCOM to VCOM_DC voltage
    # 01 - Put VCOM to VDH+VCOM_DC voltage (see PWR register config)
    # 10 - Put VCOM to VDL+VCOM_DC voltage
    # 11 - Floating / Not used.
    #
    # The VCOM table has two additional bytes at the end.
    # The meaning of these bytes apparently is the following (but I'm not
    # really sure what they mean):
    # 
    # First additional byte: ST_XON, if (1<<step) bit is set, for
    # that step all gates are on. Second byte: ST_CHV. Like ST_XON
    # but if (1<<step) bit is set, VCOM voltage is set to high for this step.
    #
    # However they are set to 0 in all the LUTs I saw, so they are generally
    # not used and we don't use it either.
    def set_waveform_lut(self,speed=None,no_flickering=None):
        if speed == None: speed = self.speed
        if no_flickering == None: no_flickering = self.no_flickering

        if speed < 1:
            # For the default speed, we don't set any LUT, but resort
            # to the one inside the device. __init__() will take care
            # to tell the chip to use internal LUTs by setting the right
            # PSR field to LUT_OTP.
            return

        if speed > 6:
            raise ValueError("Speed must be set between 0 and 6")

        # In this driver we try to do things a bit differently and compute
        # LUTs on the fly depending on the 'speed' requested by the user.
        # Each successive speed value cuts the display update time in half.
        # Floating point speeds are possible, so 2.5 will be between
        # 2 and 3 from the POV of speed and quality.
        #
        # Moreover, we check if no_flickering was set to True. In this case
        # we change the LUTs in two ways, with the goal to prevent the
        # unpleasant color inversion flickering effect:
        #
        # 1. The 2 x black-to-white ping-pong is NOT performed.
        #    This usually is performed to set the display pixels in a
        #    know state to prevent ghosting, leaving residues and so forth.
        # 2. Waveforms for white-to-white and black-to-black will avoid
        #    to invert the pixels at all. We will just set the
        #    voltage needed to confirm the pixel color.

        # We use just three tables, as for WHITE->WHITE and BLACK->BLACK
        # we will reuse the first tables, possibly modifying them on the
        # fly.
        VCOM = bytearray(44)
        BW = bytearray(42)
        WB = bytearray(42)

        # Those periods are powers of two so that each successive 'speed'
        # value cuts them in half cleanly.
        period = 64           # Num. of frames for single direction change.
        hperiod = period//2   # Num. of frames for back-and-forth change.
        
        # Actual period is scaled by the speed factor
        period = int(max(period / (2**(speed-1)), 1))
        hperiod = int(max(hperiod / (2**(speed-1)), 1))

        # Setup three (or two) steps.
        # For all the steps, VCOM is just taken at VCOM_DC,
        # so the VCOM pattern is always 0.

        row = 0
        if speed < 4:
            # Step 0: reverse pixel color compared to the target color for
            # a given period.
            self.set_lut_row(VCOM,row,pat=0,dur=[period,0,0,0],rep=1)
            self.set_lut_row(BW,row,pat=0b01_000000,dur=[period,0,0,0],rep=1)
            self.set_lut_row(WB,row,pat=0b10_000000,dur=[period,0,0,0],rep=1)
            row += 1
        if no_flickering == False or speed >= 4:
            # Step 1: reverse pixel color for half period, back to the color
            # the pixel should have. Repeat two times. This step is skipped
            # if anti flickering is no, but at high speed, since it is
            # not visible anyway.
            rep = 1 if speed >= 4 else 2
            self.set_lut_row(VCOM,row,pat=0,dur=[hperiod,hperiod,0,0],rep=rep)
            self.set_lut_row(BW,row,pat=0b01_10_0000,dur=[hperiod,hperiod,0,0],rep=rep)
            self.set_lut_row(WB,row,pat=0b01_10_0000,dur=[hperiod,hperiod,0,0],rep=rep)
            row += 1
        # Step 2: Finally set the target color for a full period.
        # Note that we want to repeat this cycle twice if we are going
        # fast or we skipped the ping-pong step, to have a more convincing
        # white/black contrast and less ghosting at the cost of a minor
        # time penalty.
        rep = 2 if speed > 3 or no_flickering else 1
        self.set_lut_row(VCOM,row,pat=0,dur=[period,0,0,0],rep=rep)
        self.set_lut_row(BW,row,pat=0b10_000000,dur=[period,0,0,0],rep=rep)
        self.set_lut_row(WB,row,pat=0b01_000000,dur=[period,0,0,0],rep=rep)

        if self.debug:
            self.show_lut(BW,"BW")
            self.show_lut(WB,"WB")

        self.write(CMD_LUT_VCOM,VCOM)
        self.write(CMD_LUT_BW,BW)
        self.write(CMD_LUT_WB,WB)

        # If no flickering mode is on, for pixels in the same state
        # as before, we perform a single frame inversion, then back
        # to the actual color.
        #
        # If no flickering mode is disabled, we use an empty
        # waveform BB and WW. Read the warning below.
        #
        # WARNING: to just re-affirm the pixel color applying only the
        # voltage needed for the target color for the normal duration
        # will result in microparticles to be semi-permanently polarized
        # towards one way, with damages that often go away in one day or
        # alike, but I guess it may ruin the display forever insisting
        # enough. So we just put the pixels to ground, and from time to
        # time do a full refresh.
        if no_flickering:
            self.clear_lut(BW)
            self.clear_lut(WB)

        if self.debug:
            self.show_lut(BW,"WW")
            self.show_lut(WB,"BB")

        self.write(CMD_LUT_WW,BW)
        self.write(CMD_LUT_BB,WB)

    # Change the speed once the driver is already initialized.
    # Sometimes in an application there are updates we want to do
    # at high quality, other updates we want to do faster.
    def set_speed(self,new_speed,no_flickering=None):
        if no_flickering != None:
            self.no_flickering = no_flickering
        self.speed = new_speed
        self.set_panel_configuration()
        self.set_waveform_lut()
        self.update_count = 0

    # Set a given row in a waveform lookup table.
    # Lookup tables are 6 rows per 7 cols, like in this
    # example:
    #
    # 0x40, 0x17, 0x00, 0x00, 0x00, 0x02,  <- step 0
    # 0x90, 0x17, 0x17, 0x00, 0x00, 0x02,  <- step 1
    # 0x40, 0x0A, 0x01, 0x00, 0x00, 0x01,  <- step 2
    # 0xA0, 0x0E, 0x0E, 0x00, 0x00, 0x02,  <- step 3
    # 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  <- step 4
    # 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  <- step 5
    # 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  <- step 6
    #
    # Fror each step the first byte encodes the 4 patterns, two bits
    # each. The next 4 bytes the duration in frames. The Final byte
    # the repetition number. See the top comment of set_waveform_lut()
    # for more info.
    def set_lut_row(self,lut,row,pat,dur,rep):
        if row > 6: raise valueError("LUTs have 7 total rows (0-6)")
        off = 6*row
        lut[off] = pat
        lut[off+1] = dur[0]
        lut[off+2] = dur[1]
        lut[off+3] = dur[2]
        lut[off+4] = dur[3]
        lut[off+5] = rep

    # Just fill the array of zero values.
    @micropython.viper
    def clear_lut(self,lut):
        l = int(len(lut))
        p = ptr8(lut)
        for i in range(l): p[i] = 0

    # Show a well-formatted LUT table. Useful for debugging.
    def show_lut(self,lut,name):
        print(name,":")
        for i in range(7):
            for j in range(6):
                print(hex(lut[i*6+j]),end=' ')
            print("")
        print("---")

    # Wait for the display to return back able to accept commands
    # (if it is updating the display it remains busy), and switch
    # it off once it is possible.
    def wait_and_switch_off(self):
        self.wait_ready()
        self.write(CMD_POF)

    # Update the screen with the current image in the framebuffer.
    # If 'fb' is passed, we use a different framebuffer instead.
    # If blocking is True, the function blocks until the update
    # is complete and powers the display off. Otherwise the display
    # will remain powered on, and can (and should) be turned off later
    # with wait_and_switch_off().
    #
    # The function returns False and does nothing in case the
    # blocking argument is False but there is an update already
    # in progress. Otherwise True is returned and the display is updated.
    def update(self,blocking=True,fb=None):
        if fb == None: fb = self.raw_fb
        if blocking == False and self.is_busy(): return False

        # At the first refresh with a no-flickering mode, and also
        # every N refreshes, do a full refresh.
        if self.update_count % self.full_update_period == 0 and \
           self.no_flickering:
            self.set_waveform_lut(min(2,self.speed),False)

        self.send_image(fb)
        self.write(CMD_DRF) # Start refresh cycle.

        # Load back the no-flickering LUTs if we forced a flickered refresh.
        if self.update_count % self.full_update_period == 0 and \
           self.no_flickering:
            self.set_waveform_lut()

        if blocking: self.wait_and_switch_off()
        self.update_count += 1
        return True

    # Transfer bitmap to device. The chip has two framebuffers, one for
    # the old image and one for the new image. This way it can do the
    # difference when performing the update and apply the correct waveform
    # depending on WW, BB, WB, BW transition. When we refresh, the new
    # framebuffer is automatically copied to the old one, but we can control
    # both framebuffer when we wish to.
    def send_image(self,fb,old=False):
        self.write(CMD_PON) # Power on
        self.write(CMD_PTOU) # Partial mode off
        if old:
            self.write(CMD_DTM1,fb) # Transfer to previous image buffer.
        else:
            self.write(CMD_DTM2,fb) # Transfer to current image buffer.
        self.write(CMD_DSP) # End of data

    # Helper function to render greyscale images.
    #
    # This function has to generate two one-bit images, using the two
    # framebuffers fb1 and fb2. For three grey levels, we set the
    # before/after bits in order to trigger the WW/BB/WB conditions,
    # so that we assign to each of this LUTs the waveform needed to
    # generate a different level of greys. We use BW for pixels that were
    # already set in past iterations and should not be toched.
    # 
    # Using this trick, we can set the pixels of three different levels
    # of greys in the same update. The image to render should be in
    # 'grey', where each byte maps to a pixel: higher values means
    # a more intense level of grey.
    #
    # The three level of greys that this function will match are
    # given by 'level': from level to level+2 inclusive.
    @micropython.viper
    def set_pixels_for_greyscale(self, grey:ptr8, fb1:ptr8, fb2:ptr8, width:int, height:int, level:int) -> int:
        count = int(width*height)
        anypixel = int(0)
        for i in range(count//8):
            fb1[i] = 0
            fb2[i] = 0

        for i in range(count):
            # Pixel that reached level "1" are the only ones at the
            # current grey level we want to set.
            byte = i >> 3
            bit = 1 << (7-(i&7))

            if grey[i] == level:        # WW condition
                anypixel = 1
                pass
            elif grey[i] == level+1:    # BB condition
                anypixel = 1
                fb1[byte] |= bit
                fb2[byte] |= bit
            elif grey[i] == level+2:    # WB condition
                anypixel = 1
                fb1[byte] |= bit
            else:                   # BW condition, pixels not touched.
                fb2[byte] |= bit
        return anypixel

    def load_greyscale_image(self,filename):
        # Configurable parameters:
        # 1. How many frames it takes for a pixel to reach full black?
        # 2. How many greys we want to generate?

        greyscale = 32 # Can't be more than 32. Try 32, 16, 8, 4.
        frames_to_black = 32

        # Read image data.
        f = open(filename,"rb")
        f.read(4)
        imgdata = bytearray(self.width*self.height)
        f.readinto(imgdata)
        print("Image max luminance:",max(imgdata))
        for i in range(len(imgdata)):
            imgdata[i] = int(((255 - imgdata[i]) / 255) * (greyscale-1))

        # Prepare the display: we want it to be white, and we want the
        # registers LUTs to be selected (all speeds but speed 0).
        orig_speed = self.speed
        orig_no_flickering = self.no_flickering

        self.set_speed(2,no_flickering=True)
        self.fb.fill(0)
        self.update(blocking=True) # All screen white

        # Nothing to do for white pixels or already black pixels.
        # Set an empty LUT.
        LUT = bytearray(42)
        VCOM = bytearray(44)

        # Now for each level of grey in the image, create a bitmap composed
        # only of pixels of that level of grey, and create an ad-hoc LUT
        # that polarizes pixels towards black for an amount of time (frames)
        # proportional to the grey level.
        fb2 = bytearray(self.width*self.height//8)
        for g in range(0,greyscale,3):
            # Resort to a faster method in Viper to set the pixels for the
            # current greyscale level.
            anypixel = self.set_pixels_for_greyscale(imgdata,self.raw_fb,fb2,self.width,self.height,g+1)
            if anypixel:
                # Transfer the "old" image, so that for difference
                # with the new we transfer via .update() we create
                # the four set of conditions (WW, BB, WB, BW) based
                # on the difference between the bits in the two
                # images.
                self.send_image(fb2,old=True)

                # We set the framebuffer with just the pixels of the level
                # of grey we are handling in this cycle, so now we apply
                # the voltage for a time proportional to this level (see
                # the setting of LUT[1], that is the number of frames).
                LUT[0] = 0x55 # Go black
                LUT[5] = 1 # Repeat 1 for all
                LUT[1] = int(frames_to_black/greyscale*(g+1))
                self.write(CMD_LUT_WW,LUT)
                LUT[1] = int(frames_to_black/greyscale*(g+2))
                self.write(CMD_LUT_BB,LUT)
                LUT[1] = int(frames_to_black/greyscale*(g+3))
                self.write(CMD_LUT_WB,LUT)
                LUT[1] = 0 # These pixels will be unaffected, none of them
                           # is of the three colors handled in this cycle.
                LUT[5] = 0
                self.write(CMD_LUT_BW,LUT)

                # Minimal VCOM LUT to avoid any unneeded wait.
                VCOM[0] = 0 # Already zero, just to make it obvious.
                VCOM[1] = int(frames_to_black/greyscale*(g+3))
                VCOM[5] = 1
                self.write(CMD_LUT_VCOM,VCOM)

                # Finally update.
                self.update(blocking=True)

        # Restore a normal LUT based on configured speed.
        self.set_speed(orig_speed,no_flickering=orig_no_flickering)

    # Fade off effect.
    def fade_out(self,blocking=True):
        LUT = bytearray(42)
        VCOM = bytearray(44)
        LUT[0] = 0b10_00_00_00
        LUT[1] = 1 # Frames
        LUT[2] = 2 # Frames
        LUT[3] = 2 # Frames
        LUT[4] = 2 # Frames
        LUT[5] = 10 # Repeat

        LUT[6] = 0b10_00_00_00
        LUT[7] = 3 # Frames
        LUT[11] = 10 # Repeat

        VCOM[1:6] = LUT[1:6]
        VCOM[7:12] = LUT[7:12]
        self.write(CMD_LUT_VCOM,VCOM)
        self.write(CMD_LUT_WW,LUT)
        self.write(CMD_LUT_BB,LUT)
        self.write(CMD_LUT_WB,LUT)
        self.write(CMD_LUT_BW,LUT)
        empty = bytes(self.width*self.height//8)
        self.update(blocking=blocking,fb=empty)
        self.set_waveform_lut()

if  __name__ == "__main__":
    from machine import SPI
    import random

    spi = SPI(0, baudrate=12000000, phase=0, polarity=0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    eink = UC8151(spi,cs=17,dc=20,rst=21,busy=26,speed=2,no_flickering=False)

    eink.load_greyscale_image("dama.grey")
    #eink.load_greyscale_image("hopper.grey")
    STOP

    # eink.set_handmade_lut()

    for speed in [2,3,4.3,5]:
        for noflick in [False,True]:
            # Reconfig
            eink.speed = speed
            eink.no_flickering = noflick
            eink.set_waveform_lut()

            random.seed(123)
            for _ in range(4):
                eink.fb.text(f"Speed:{speed}",2,0)
                eink.fb.text(f"No_Flick:{noflick}",2,10)
                x = random.randrange(100)
                y = 80+random.randrange(100)
                eink.fb.text("TEST",x,y,1)
                eink.fb.ellipse(x,y,50,30,1)
                eink.fb.fill_rect(x,y+50,50,50,1)
                start = time.ticks_ms()
                eink.update(blocking=True)
                update_time = time.ticks_ms() - start
                print("Update time:",update_time)
                eink.fb.fill(0)
                eink.fb.text(f"delay MS:{update_time}",10,25)
                time.sleep(1)
