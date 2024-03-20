This utility converts PNG images into 'gs8' files, that is an uncompressed
representation of the image with a simple 4 bytes header:

```
+-------+--------+----------//
| width | heigth |  Image data... each byte between 0 - 255
+-------+--------+----------//
```

Width and height are big endian unsigned 16 bit integers.
The converted images can be loaded by this driver and displayed on
the screen.

Compile with `make`, then:

    ./png2gs8 dama_ermellino.png dama.gs8

Then use the converted file as explained in the documentation for the driver.
