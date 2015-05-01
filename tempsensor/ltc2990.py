#!/usr/bin/python -x
#
# Basic class to handle gathering temperature from the
# LTC2990
# Chris Hauser
#

import smbus
from time import sleep

class LTC:

    LTC_STATUS_REG = 0x00         # Indicates busy state and conversion status
    LTC_CONTROL_REG = 0x01        # Controls mode, Single/Repeat, Celsius/Kelvin
    LTC_TRIGGER_REG = 0x02        # Triggers conversion
    LTC_TINT_MSB_REG = 0x04       # Internal Temperature MSB
    LTC_TR1_TR2 = 0x05            # read TR1 and TR2
    LTC_V1_MSB_REG = 0x06         # V1, V1-V2, or TR_1 T MSB
    LTC_V1_LSB_REG = 0x07         # V1, V1-V2, or TR_1 T LSB
    LTC_MODE_MASK = 0x07          # use when changing modes
    LTC_TIMEOUT = 1000            # milliseconds
    LTC_KELVIN_ENABLE = 0x80      # Kelvin
    LTC_CELSIUS_ENABLE = 0x00     # Celsius
    LTC_TEMPERATURE_LSB = 0.0625  # Conversion factor
    ADDRESS = 0x4C                # I2C chip address
    RUN_MODE = 0x5F
    bus = None

    def __init__(self):
        """
        Selects bus and sets initial mode
        :return:
        """
        self.bus = smbus.SMBus(1)   # 512-MB RPi the bus is 1. Otherwise, bus is 0.
        self.bus.write_byte_data(self.ADDRESS, self.LTC_CONTROL_REG, self.RUN_MODE)
        # triggers a conversion by writing any value to the trigger register
        self.bus.write_byte_data(self.ADDRESS, self.LTC_TRIGGER_REG, 0x00)

    def register_set_clear_bits(self, i2c_addr, register_addr, bits_to_set, bits_to_clear):
        """
         only used for mode changes.
        :param i2c_addr:
        :param register_addr:
        :param bits_to_set: Assuming 3 bits
        :param bits_to_clear: Assuming 3 bits
        :return:
        """
        rdata = self.bus.read_byte_data(i2c_addr, register_addr)
        rdata = rdata & (~bits_to_clear)
        rdata = rdata | bits_to_set
        self.bus.write_byte_data(i2c_addr, register_addr, rdata)

    def adc_read_new_data(self, i2c_addr, msb_register_addr, timeout):
        """
        Attempts to read a word value from the register
        :param i2c_addr:
        :param msb_register_addr:
        :param timeout:
        :return:
        """
        status_bit = msb_register_addr/2-1
        return self.adc_read_timeout(i2c_addr, msb_register_addr, timeout, status_bit)

    def adc_read_timeout(self, i2c_addr, msb_register_addr, timeout, status_bit):
        """
        Waits for the specified timeout, or valid data before taking a reading from
        the register
        :param i2c_addr:
        :param msb_register_addr:
        :param timeout:
        :param status_bit:
        :return:
        """
        for count in range(1, timeout):
            reg_data = self.bus.read_byte_data(self.ADDRESS, self.LTC_STATUS_REG)
            if 1 == ((reg_data >> status_bit) & 0x1):
                print 'Status bit set'
                break
            sleep(.001)  # delay 1 millisecond
        return self.adc_read(i2c_addr, msb_register_addr)

    def adc_read(self, i2c_addr, msb_register_addr):
        """
        Reads a word value from the register, and returns the value along with
        the registers valid bit
        :param i2c_addr:
        :param msb_register_addr:
        :return:
        """
        msb = self.bus.read_byte_data(i2c_addr, msb_register_addr)
        msb <<= 8
        lsb = self.bus.read_byte_data(i2c_addr, msb_register_addr+1)
        code = msb | lsb
        data_valid = ((code >> 15) & 0x01)  # place data valid bit in data_valid
        return data_valid, code

    def temperature(self, adc_code, temperature_lsb, unit):
        """
        Calculates the temperature by removing the top 3 bits
        representing Data Valid, Sensor Short and Sensor Open
        and multiplying by the given factor.
        NOTE: Since Kelvin cannot be negative, then we need to
        account for the sign bit if the measurement is in Celsius
        :param adc_code:
        :param temperature_lsb:
        :return:
        """
        code = (adc_code & 0x1FFF)  # removes first 3 bits
        if unit is False:
            if code >> 12:
                adc_code = (code | 0xE000)
                print 'Extending sign'
        temp = adc_code * temperature_lsb
        return temp

    def is_celsius(self):
        reg_data = self.bus.read_byte_data(self.ADDRESS, self.LTC_CONTROL_REG)
        if (reg_data >> 15) & 0x1:
            return False
        return True

    def gather_v1_temperature(self):
        """
        Gathers the v1 temperature
        NOTE: The correct mode must be set
        :return:
        """
            
        # take fresh reading
        (data_valid, adc_code) = self.adc_read_new_data(self.ADDRESS, self.LTC_V1_MSB_REG, self.LTC_TIMEOUT)
        (data_valid, adc_code) = self.adc_read(self.ADDRESS, self.LTC_V1_MSB_REG)
        return self.temperature(adc_code, self.LTC_TEMPERATURE_LSB, self.is_celsius())

    def gather_int_temperature(self):
        """
        Gathers the internal temperature
        NOTE: The correct mode for gathering the internal temperature
        must be set
        :return:
        """

        # take fresh reading
        (data_valid, adc_code) = self.adc_read_new_data(self.ADDRESS, self.LTC_TINT_MSB_REG, self.LTC_TIMEOUT)
        (data_valid, adc_code) = self.adc_read(self.ADDRESS, self.LTC_TINT_MSB_REG)
        return self.temperature(adc_code, self.LTC_TEMPERATURE_LSB, self.is_celsius())

ltc = LTC()
print "Internal Temperature %f" % ltc.gather_int_temperature()
print "V1 Temperature %f" % ltc.gather_v1_temperature()
