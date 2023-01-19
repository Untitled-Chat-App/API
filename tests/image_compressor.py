import os
import time
import numpy
from PIL import Image


def compress(input_filename, output_file_name):
    # for measuring run time
    start_time = time.perf_counter()
    start_size = os.stat(input_filename).st_size

    # the compressed image result must be bellow this size:
    MB_SIZE = 1500000  # this is in bytes

    # open image and resize to 1000x1000
    image = Image.open(input_filename).convert("RGB").resize((1000, 1000))

    # create numpy array with all pixels
    pixel_values = numpy.asarray(image)

    # round each pixel down -1  eg 53 -> 50
    new_pixel_values = numpy.round(pixel_values, -1)
    image = Image.fromarray(new_pixel_values, "RGB")

    # save image to file
    image.save(output_file_name, "JPEG")

    # check size of output image
    filesize = os.stat(output_file_name).st_size

    # if after all that rounding the image is still not under the size:
    if filesize > MB_SIZE:
        diff = filesize - MB_SIZE

        # percentage needed to make image under size
        percentage = 100 - int(diff / (filesize / 100))

        # reduce quality of image by percentage to reach file size
        image.save(output_file_name, optimize=True, quality=percentage)

    # new size of image
    new_size = os.stat(output_file_name).st_size

    image.close()

    # stats
    print(
        f"Image has been compressd!\nOld file size: {round(start_size / 1e6, 2)}mb\
            \nNew file size: {round(new_size / 1e6, 2)}mb",
    )
    print("Time Took:", round(time.perf_counter() - start_time, 2), "seconds")


if __name__ == "__main__":
    # input image should be a square
    compress("input.jpg", "output.jpeg")
