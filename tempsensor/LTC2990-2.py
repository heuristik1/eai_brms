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
    LTC_CONTROL_REG = 0x5D        # Controls mode, Single/Repeat, Celsius/Kelvin
    LTC_TRIGGER_REG = 0x02        # Triggers conversion
    LTC_TINT_MSB_REG = 0x04       # Internal Temperature MSB
    LTC_TR1_TR2 = 0x05            # read TR1 and TR2
    LTC_V1_MSB_REG = 0x06         # V1, V1-V2, or TR_1 T MSB
    LTC_V3_MSB_REG = 0x0A         # V3, V3-V4, or TR_2 T MSB
    LTC_V1_LSB_REG = 0x07         # V1, V1-V2, or TR_1 T LSB
    LTC_V3_LSB_REG = 0x0B         # V3, V3-V4, or TR_2 T LSB
    LTC_VOLTAGE_MODE_MASK = 0x07  # use when changing modes
    LTC_TIMEOUT = 1000            # milliseconds
    LTC_KELVIN_ENABLE = 0x80      # Kelvin
    LTC_CELSIUS_ENABLE = 0x00     # Celsius
    LTC_TEMP_FORMAT_MASK = 0x18  # Use mask when changing formats
    LTC_TEMPERATURE_LSB = 0.0625  # Conversion factor
    ADDRESS = 0x4c                # I2C chip address
    bus = None

    def __init__(self):
        self.bus = smbus.SMBus(1)   # 512-MB RPi the bus is 1. Otherwise, bus is 0.

    def enable_temp_mode(self):
        # enable temperature mode
        self.register_set_clear_bits(self.ADDRESS, self.LTC_CONTROL_REG, self.LTC_TR1_TR2, self.LTC_VOLTAGE_MODE_MASK)
        print 'Temperature mode enabled'

    def enable_celsius_mode(self):
        self.register_set_clear_bits(self.ADDRESS, self.LTC_CONTROL_REG, self.LTC_CELSIUS_ENABLE, self.LTC_TEMP_FORMAT_MASK)
        print 'Celsius mode enabled'

    def register_set_clear_bits(self, i2c_addr, register_addr, bits_to_set, bits_to_clear):
        rdata = self.bus.read_byte_data(i2c_addr, register_addr)
        rdata = rdata & (~bits_to_clear)
        rdata = rdata | bits_to_set
        self.bus.write_byte_data(i2c_addr, register_addr, rdata)

    def adc_read_new_data(self, i2c_addr, msb_register_addr, timeout):
        status_bit = msb_register_addr/2-1
        self.adc_read_timeout(i2c_addr, msb_register_addr, timeout, status_bit)  # throw away old
        return self.adc_read_timeout(i2c_addr, msb_register_addr, timeout, status_bit)  # gather new

    def adc_read_timeout(self, i2c_addr, msb_register_addr, timeout, status_bit):
        for count in range(0, timeout):
            reg_data = self.bus.read_byte_data(self.ADDRESS, self.LTC_STATUS_REG)
            if 1 == ((reg_data >> status_bit) & 0x1):
                print 'Status bit set'
                break
            sleep(.001)  # delay 1 millisecond
        return self.adc_read(i2c_addr, msb_register_addr)

    def adc_read(self, i2c_addr, msb_register_addr):
        code = self.bus.read_word_data(i2c_addr, msb_register_addr)
        data_valid = ((code >> 15) & 0x01)  # place data valid bit in data_valid
        adc_code = (code & 0x7fff)  # removes data valid bit and returns adc code
        return data_valid, adc_code

    def temperature(self, adc_code, temperature_lsb, unit):
        adc_code = (adc_code & 0x1FFF)  # removes first 3 bits
        if unit is False:
            print 'Mode is Celcius'
            if adc_code >> 12:
                print 'Extending sign'
                adc_code = (adc_code | 0xE000)
        temp = float(adc_code) * temperature_lsb
        return temp

    def gather_TINT_temperature(self):
        # triggers a conversion by writing any value to the trigger register
        self.bus.write_byte_data(self.ADDRESS, self.LTC_TRIGGER_REG, 0x00)

        # flush one adc reading in case it is stale
        self.adc_read_new_data(self.ADDRESS, self.LTC_TINT_MSB_REG, self.LTC_TIMEOUT)

        # take fresh reading
        (data_valid, adc_code) = self.adc_read_new_data(self.ADDRESS, self.LTC_TINT_MSB_REG, self.LTC_TIMEOUT)

        reg_data = self.bus.read_byte_data(self.ADDRESS, self.LTC_CONTROL_REG)
        is_kelvin = False
        if reg_data & self.LTC_KELVIN_ENABLE:
            is_kelvin = True
            print "Kelvin Enabled"
        return self.temperature(adc_code, self.LTC_TEMPERATURE_LSB, is_kelvin)
 
    def gather_TR1_temperature(self):
        # triggers a conversion by writing any value to the trigger register
        self.bus.write_byte_data(self.ADDRESS, self.LTC_TRIGGER_REG, 0x00)

        # flush one adc reading in case it is stale
        self.adc_read_new_data(self.ADDRESS, self.LTC_V1_MSB_REG, self.LTC_TIMEOUT)

        # take fresh reading
        (data_valid, adc_code) = self.adc_read_new_data(self.ADDRESS, self.LTC_V1_MSB_REG, self.LTC_TIMEOUT)

        reg_data = self.bus.read_byte_data(self.ADDRESS, self.LTC_CONTROL_REG)
        is_kelvin = False
        if reg_data & self.LTC_KELVIN_ENABLE:
            is_kelvin = True
            print "Kelvin Enabled"
        return self.temperature(adc_code, self.LTC_TEMPERATURE_LSB, is_kelvin)
    
    def gather_TR2_temperature(self):
        # triggers a conversion by writing any value to the trigger register
        self.bus.write_byte_data(self.ADDRESS, self.LTC_TRIGGER_REG, 0x00)

        # flush one adc reading in case it is stale
        self.adc_read_new_data(self.ADDRESS, self.LTC_V3_MSB_REG, self.LTC_TIMEOUT)

        # take fresh reading
        (data_valid, adc_code) = self.adc_read_new_data(self.ADDRESS, self.LTC_V3_MSB_REG, self.LTC_TIMEOUT)

        reg_data = self.bus.read_byte_data(self.ADDRESS, self.LTC_CONTROL_REG)
        is_kelvin = False
        if reg_data & self.LTC_KELVIN_ENABLE:
            is_kelvin = True
            print "Kelvin Enabled"
        return self.temperature(adc_code, self.LTC_TEMPERATURE_LSB, is_kelvin)

ltc = LTC()
ltc.enable_temp_mode()
ltc.enable_celsius_mode()
print "TINT Temperature %f" % ltc.gather_TINT_temperature()
print "TR1 Temperature %f" % ltc.gather_TR1_temperature()
print "TR2 Temperature %f" % ltc.gather_TR2_temperature()
