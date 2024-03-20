/* Copyright (c) 2024, Salvatore Sanfilippo <antirez at gmail dot com>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *   * Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#define PNG_DEBUG 3
#include <png.h>

/* Convert the PNG to into a raw RGB565 image that can be directly
 * written to the ST77xx chip. The only added header is a composed of
 * two 16 bit unsigned integers in big endian, width and height.
 * The number of bytes of the image is always 4 + width*height*2 */
#define PNG_BYTES_TO_CHECK 8
void convert_png(char *iname, char *oname) {
    unsigned char buf[PNG_BYTES_TO_CHECK];
    png_structp png_ptr;
    png_infop info_ptr;
    png_uint_32 width, height, j;
    int color_type;

    /* Open the images for reading/writing. */
    FILE *ifp = fopen(iname,"r");
    if (ifp == NULL) {
        perror("Opening input image");
        exit(1);
    }
    FILE *ofp = fopen(oname,"w");
    if (ofp == NULL) {
        perror("Opening output image");
        exit(1);
    }

    /* Check signature */
    if (fread(buf, 1, PNG_BYTES_TO_CHECK, ifp) != PNG_BYTES_TO_CHECK ||
        png_sig_cmp(buf, (png_size_t)0, PNG_BYTES_TO_CHECK))
    {
        fprintf(stderr,"Invalid PNG file");
        return;
    }

    /* Initialize data structures */
    png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING,
        NULL,NULL,NULL);
    if (png_ptr == NULL) {
        perror("png_create_read_struct()");
        exit(1);
    }

    info_ptr = png_create_info_struct(png_ptr);
    if (info_ptr == NULL) {
        perror("png_create_info_struct()");
        exit(1);
    }

    /* Error handling code */
    if (setjmp(png_jmpbuf(png_ptr)))
    {
        perror("setjmp() failed");
        exit(1);
    }

    /* Set the I/O method */
    png_init_io(png_ptr, ifp);

    /* Undo the fact that we read some data to detect the PNG file */
    png_set_sig_bytes(png_ptr, PNG_BYTES_TO_CHECK);

    /* Read the PNG in memory at once */
    png_read_png(png_ptr, info_ptr, PNG_TRANSFORM_EXPAND, NULL);
    width = png_get_image_width(png_ptr, info_ptr);
    height = png_get_image_height(png_ptr, info_ptr);
    color_type = png_get_color_type(png_ptr, info_ptr);

    /* Write output image header. */
    unsigned char hdr[4];
    hdr[0] = width>>8;
    hdr[1] = width&0xff;
    hdr[2] = height>>8;
    hdr[3] = height&0xff;
    if (fwrite(hdr,4,1,ofp) != 1) {
        perror("Writing to output file)");
        exit(1);
    }

    char *color_str = "unknown";
    switch(color_type) {
    case PNG_COLOR_TYPE_RGB: color_str = "RGB"; break;
    case PNG_COLOR_TYPE_RGB_ALPHA: color_str = "RGBA"; break;
    case PNG_COLOR_TYPE_GRAY: color_str = "GRAY"; break;
    case PNG_COLOR_TYPE_GRAY_ALPHA: color_str = "GRAYA"; break;
    case PNG_COLOR_TYPE_PALETTE: color_str = "PALETTE"; break;
    }

    fprintf(stderr,"%dx%d image, color:%s\n",(int)width,(int)height,color_str);
    if (color_type != PNG_COLOR_TYPE_RGB &&
        color_type != PNG_COLOR_TYPE_RGB_ALPHA &&
        color_type != PNG_COLOR_TYPE_GRAY &&
        color_type != PNG_COLOR_TYPE_GRAY_ALPHA)
    {
        fprintf(stderr,"Unsupported PNG color type.");
        exit(1);
    }

    /* Get the image data */
    unsigned char **imageData = png_get_rows(png_ptr, info_ptr);

    for (j = 0; j < height; j++) {
        unsigned char *src = imageData[j];
        unsigned int i, r, g, b;

        for (i = 0; i < width; i++) {
            if (color_type == PNG_COLOR_TYPE_RGB_ALPHA ||
                color_type == PNG_COLOR_TYPE_RGB)
            {
                r = src[0];
                g = src[1];
                b = src[2];
                src += (color_type == PNG_COLOR_TYPE_RGB_ALPHA) ? 4 : 3;
            } else if (color_type == PNG_COLOR_TYPE_GRAY_ALPHA ||
                       color_type == PNG_COLOR_TYPE_GRAY)
            {
                r = b = g = src[0];
                src += (color_type == PNG_COLOR_TYPE_GRAY_ALPHA) ? 2 : 1;
            }
            double lum = 0.299*r + 0.587*g + 0.114*b;
            buf[0] = (int)lum;
            if (fwrite(buf,1,1,ofp) != 1) {
                perror("Writing to output file)");
                exit(1);
            }
        }
    }

    /* Free the image and resources and return */
    png_destroy_read_struct(&png_ptr, &info_ptr, NULL);
    fclose(ifp);
    fclose(ofp);
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr,"Usage: %s image.png image.565\n",argv[0]);
        exit(1);
    }
    convert_png(argv[1],argv[2]);
    return 0;
}
