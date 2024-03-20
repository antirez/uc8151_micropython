all: png2gs8

png2gs8: png2gs8.c
	$(CC) -O2 png2gs8.c `libpng-config --cflags` `libpng-config --L_opts` `libpng-config --libs` -lm -o png2gs8 -Wall -W

clean:
	rm -f png2gs8
