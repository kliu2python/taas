# pylint: disable=too-many-statements
import time

import numpy as np
from singleton_decorator import singleton

from . import base


@singleton
class Display(base.DriverBase):
    width = 240
    height = 240

    def command(self, cmd):
        self.digital_write(self.dc_pin, self.gpio.LOW)
        self.spi_writebyte([cmd])

    def data(self, val):
        self.digital_write(self.dc_pin, self.gpio.HIGH)
        self.spi_writebyte([val])

    def reset(self):
        self.gpio.output(self.rst_pin, self.gpio.HIGH)
        time.sleep(0.01)
        self.gpio.output(self.rst_pin, self.gpio.LOW)
        time.sleep(0.01)
        self.gpio.output(self.rst_pin, self.gpio.HIGH)
        time.sleep(0.01)

    def init(self):
        self.driver_init()
        self.reset()

        self.command(0x36)
        self.data(0x00)

        self.command(0x3A)
        self.data(0x05)

        self.command(0x21)

        self.command(0x2A)
        self.data(0x00)
        self.data(0x00)
        self.data(0x01)
        self.data(0x3F)

        self.command(0x2B)
        self.data(0x00)
        self.data(0x00)
        self.data(0x00)
        self.data(0xEF)

        self.command(0xB2)
        self.data(0x0C)
        self.data(0x0C)
        self.data(0x00)
        self.data(0x33)
        self.data(0x33)

        self.command(0xB7)
        self.data(0x35)

        self.command(0xBB)
        self.data(0x1F)

        self.command(0xC0)
        self.data(0x2C)

        self.command(0xC2)
        self.data(0x01)

        self.command(0xC3)
        self.data(0x12)

        self.command(0xC4)
        self.data(0x20)

        self.command(0xC6)
        self.data(0x0F)

        self.command(0xD0)
        self.data(0xA4)
        self.data(0xA1)

        self.command(0xE0)
        self.data(0xD0)
        self.data(0x08)
        self.data(0x11)
        self.data(0x08)
        self.data(0x0C)
        self.data(0x15)
        self.data(0x39)
        self.data(0x33)
        self.data(0x50)
        self.data(0x36)
        self.data(0x13)
        self.data(0x14)
        self.data(0x29)
        self.data(0x2D)

        self.command(0xE1)
        self.data(0xD0)
        self.data(0x08)
        self.data(0x10)
        self.data(0x08)
        self.data(0x06)
        self.data(0x06)
        self.data(0x39)
        self.data(0x44)
        self.data(0x51)
        self.data(0x0B)
        self.data(0x16)
        self.data(0x14)
        self.data(0x2F)
        self.data(0x31)
        self.command(0x21)

        self.command(0x11)

        self.command(0x29)

    def set_window(self, xstart, ystart, xend, yend):
        self.command(0x2A)
        self.data(xstart >> 8)
        self.data(xstart & 0xff)
        self.data(xend >> 8)
        self.data((xend - 1) & 0xff)

        self.command(0x2B)
        self.data(ystart >> 8)
        self.data((ystart & 0xff))
        self.data(yend >> 8)
        self.data((yend - 1) & 0xff)

        self.command(0x2C)

    def show_img(self, img):
        img_width, img_height = img.size
        if img_width == self.height and img_height == self.width:
            img = np.asarray(img)
            pix = np.zeros((self.width, self.height, 2), dtype=np.uint8)
            pix[..., [0]] = np.add(np.bitwise_and(img[..., [0]], 0xF8),
                                   np.right_shift(img[..., [1]], 5))
            pix[..., [1]] = np.add(
                np.bitwise_and(np.left_shift(img[..., [1]], 3), 0xE0),
                np.right_shift(img[..., [2]], 3))
            pix = pix.flatten().tolist()

            self.command(0x36)
            self.data(0x70)
            self.set_window(0, 0, self.height, self.width)
        else:
            img = np.asarray(img)
            pix = np.zeros((img_height, img_width, 2), dtype=np.uint8)

            pix[..., [0]] = np.add(
                np.bitwise_and(img[..., [0]], 0xF8),
                np.right_shift(img[..., [1]], 5))
            pix[..., [1]] = np.add(
                np.bitwise_and(np.left_shift(img[..., [1]], 3), 0xE0),
                np.right_shift(img[..., [2]], 3)
            )

            pix = pix.flatten().tolist()

            self.command(0x36)
            self.data(0x00)
            self.set_window(0, 0, self.width, self.height)

        self.digital_write(self.dc_pin, self.gpio.HIGH)
        for i in range(0, len(pix), 4096):
            self.spi_writebyte(pix[i:i + 4096])

    def clear(self):
        _buffer = [0xff] * (self.width * self.height * 2)
        self.set_window(0, 0, self.width, self.height)
        self.digital_write(self.dc_pin, self.gpio.HIGH)
        for i in range(0, len(_buffer), 4096):
            self.spi_writebyte(_buffer[i:i + 4096])
