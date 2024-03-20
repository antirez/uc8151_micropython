IMPORTANT: Open an issue before starting to work on one of these items to make sure there is yet interest and to agree about a potential design, in order to make more likely your change gets merged. Items here can be just random ideas, noted to avoid forgetting, but their presence does not automatically mean it's a good idea for this driver to get support for them.

## General

* Landscape mode: use Viper to invert the FB. This should also work for framebuffer modes different than 1bit of color, so if self.landscape is true, we should also rotate GS4/GS2 FBs. Transpose the FBs in place, without allocating anything, just swapping the pixels as needed, and then swapping them again. ALTERNATIVE APPROACH: don't care about swapping and provide a simple font primitive built-in, so that it is possible to write the font in the four possible orientations. The other primitives don't need any rotation anyway.
* Allow to initialize the display in "long life" setting, where the VDL/VDH voltages are set to even lower levels.

## Greyscale mode

* Option to do a full refresh in both directions (the first inverted image, black background and inverted waveforms) for greyscale rendering, so that it's charge-neutral even in this case. But before, test what happens if we display again and again the same image. Are there burn-ins?
* Provide a way to render a `framebuf.GS4_HMSB` or `GS2` as 16/4 level of greys. Provide a ways to blit .grey images into the FB, even windowed blits.
