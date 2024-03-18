This is a MicroPython driver for the Badger 2040 eink display and other displays based on the UC8151 / IL0373 chip (these are two names for the same chip). This implementation was written using as references:

1. The original Pimoroni [C++ driver](https://github.com/pimoroni/pimoroni-pico/blob/main/drivers/uc8151/uc8151.cpp) for the Badger 2040.
2. The UC8151 chip datasheet that [can be found here](https://cdn.shopify.com/s/files/1/0174/1800/files/ED029TC1_Final_v3.0_20161012.pdf) but looks somewhat a reserved document.
3. The IL0373 chip datasheet that is included in this repository, and is a better resource than the UC8151 datasheet.
3. [This very useful gist](https://gist.github.com/joeycastillo/4cad38cc8e5cb3d5010265bc1bbd92ba) describing the LUTs layout. The same description is provided in the IL0373 chip datasheet, but the gist is a bit more a tutorial, in case it's the first time you approach e-ink displays and their lookup tables.
4. Other random bits on the internet, of course.

This driver is a bit different compared to other drivers for the same display:

* It uses computed lookup tables (LUTs) for all update speeds great than zero (for speed 0, internal OTP LUTs are used). Normally drivers use fixed LUTs tables obtained by other drivers, application notes or hand-made. Computed LUTs allow to provide more refresh modes with different compromises between quality and speed (the speed parameter can be floating point, like 2.5). This approach also uses less MicroPython memory, and makes experimenting with different refresh startegies much easier.
* Anti-flickering refresh modes. If this option is selected, waveform LUTs are modified for special modes where the display will not flicker like normally done by e-ink screens during all-screen updates. This is at the cost of minor ghosting (the severity of ghosting depends on speed). I just happen to hate the flickering much more than the delay of EPDs, and in general for many applications (imagine a clock) the flickering ruins the party.
* This driver supports displaying images with **up to 32 levels of greys!**, even if the display itself is monochome. The technique I used is documented below.
* The driver is commented in the details of what it does with the chip. So reading it you can learn how the display is setup and used.
* The fast modes still use 100HZ in this driver, not the 200HZ mode: it works better in my tests and may be easier on the display hardware.
* We use +10V high/low voltage, and the common voltage is set to the default value as well. Other drivers use 11V and/or different DCOM voltage, and may stress the hardware more.

Other then the above technical changes, the goal of this driver, especially for the MicroPython users, is to provide an alternative to the official Badger software in order to use the latest official Rasperry Pico MicroPython installs. The Badger software provided by Pimoroni is cool, but if you want to do your own project with the display, using updated MicroPython versions and maximum freedom, to have a stand-alone pure-MP driver is handy.

Moreover, given that the Badger sold many units, it's a way to make sure that this hardware will not go into obsolescence in the future, even if the seller software support will be discontinued at some point.

# Usage

```python
spi = SPI(0, baudrate=12000000, phase=0, polarity=0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
eink = UC8151(spi,cs=17,dc=20,rst=21,busy=26)

# Then write something into the framebuffer and update the display.
eink.fb.text("Test",10,10,1)
eink.update()
```

The driver allocates a framebuffer in the `fb` attribute of the object, so you dan draw into it with and call `update()` when you wish in order to refresh the display, see the MicroPython framebuffer class documentation to check all the drawing primitives you have at your disposal.

## Partial updates

TODO

## Displaying greyscale images

TODO:
* .gs8 image example.
* framebuffer example.

## Speed and flickering settings

TODO: List different speeds, times, the kind of strategy used by LUTs and so forth.

# How greyscale images are obtained

The e-paper display on the badger (and many other cheap EPDs) use chips that are not able to display different levels of greys. To do so, they would require to have separated waveform lookup tables for different levels of greys, more on-chip memory available, and so forth. However these displays are physically capable of pruducing pixels with a mix of white and black microparticles exactly like greyscale capable displays.

This driver creates ad-hoc lookup tables that will drive pixels half-way from white to black, depending on the grey to be obtained, one grey after the other, not touching the pixels already set to a different level of grey. To speedup things 3x, a trick is used: the display can update four sets of pixels at the same time, depending on the state change between the OLD and NEW bitmap images stored inside the display video memory. We can provide four different LUTS for the transition from white to white, black to white and so forth (WW, BB, WB, BW). This means that we can set three differnet greys at the same time, and use one of the transition for the pixels that are already set.

So to set for example 16 levels of greys:

1. For each loop, three different grey levels are identified.
2. Two 1-bit framebuffers are created, setting the old/new pixel state so that each grey is identified by one of the possible state changes (`1->0`, `0->1`, `1->1`, `0->0`).
3. Four different LUTs are setup: one for each of the three levels of grey and one that does nothing (for pixels of a grey level not in the three levels we are handling).
4. We repeat step 1 until all the grey levels in the image are set.

# List of supported displays

This is a list of displays brands / names supported by this driver.
Please if your dispaly works, send a pull request or just open an issue
to include it. The list is useful because this driver uses advanced techniques
and waveforms that not may work in all the displays **even if the display is based on the supported chip** (an exception is when using speed 0 and no greyscale features: in this case the internal display lookup tables are used).
For the above reasons, this list should include only displays that were actaully tested by users.

* Pomoroni Badger 2040
* Pomoroni Pico Inky Pack.
