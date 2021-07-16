# pylint: disable=too-many-instance-attributes,too-many-arguments
import time

import spidev
import RPi.GPIO


class DriverBase:
    def __init__(self, spi_freq=40000000, rst=27,
                 dc=25, bl=18, bl_freq=1000):
        self.spi = spidev.SpiDev(0, 0)
        self.rst_pin = rst
        self.dc_pin = dc
        self.bl_pin = bl
        self.speed = spi_freq
        self.bl_freq = bl_freq
        self.gpio = RPi.GPIO
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setwarnings(False)
        self.gpio.setup(self.rst_pin, self.gpio.OUT)
        self.gpio.setup(self.dc_pin, self.gpio.OUT)
        self.gpio.setup(self.bl_pin, self.gpio.OUT)
        self.gpio.output(self.bl_pin, self.gpio.HIGH)
        self._pwm = self.gpio.PWM(self.bl_pin, self.bl_freq)
        if self.spi is not None:
            self.spi.max_speed_hz = spi_freq
            self.spi.mode = 0b00

    def digital_write(self, pin, value):
        self.gpio.output(pin, value)

    def digital_read(self, pin):
        return self.gpio.input(pin)

    def spi_writebyte(self, data):
        if self.spi is not None:
            self.spi.writebytes(data)

    def driver_init(self):
        self.gpio.setup(self.rst_pin, self.gpio.OUT)
        self.gpio.setup(self.dc_pin, self.gpio.OUT)
        self.gpio.setup(self.bl_pin, self.gpio.OUT)
        self._pwm.start(100)
        if self.spi is not None:
            self.spi.max_speed_hz = self.speed
            self.spi.mode = 0b00
        return 0

    def driver_exit(self):
        if self.spi is not None:
            self.spi.close()

        self.gpio.output(self.rst_pin, 1)
        self.gpio.output(self.dc_pin, 0)
        self._pwm.stop()
        time.sleep(0.001)
        self.gpio.output(self.bl_pin, 0)
