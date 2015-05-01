#!/usr/bin/python -x
#
# Basic class to handle gathering temperature from the
# w1 devices
# Chris Hauser
#

import os
import glob
import time
import threading
import logging

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

class ReadTemp(threading.Thread):

    BASE_DIR = '/sys/bus/w1/devices/'
    FOLDER_PATTERN = '28-'
    DEVICE_FILE = 'w1_slave'
    CONFIG_FILE = 'config.properties'

    device_paths = []
    device_labels = dict()

    stop = None

    level = logging.WARN
    logfile = 'temp.log'

    def __init__(self):
        super(ReadTemp, self).__init__()
        self.stop = threading.Event()
        self.read_config()
        path = self.BASE_DIR+self.FOLDER_PATTERN+"*"
        devices = glob.glob(path)
        for idx, item in enumerate(devices):
            device_loc = item.find(self.FOLDER_PATTERN)
            if device_loc != -1:
                device = item[(device_loc+3):]
                logging.DEBUG("Discovered device %s" % self.get_device_label(device))
                item += "/" + self.DEVICE_FILE
                self.device_paths.append((device, item))

    def init_logging(self):
        numeric_level = getattr(logging, loglevel.upper(), None)
        if isinstance(numeric_level, int):
            self.level = numeric_level
            logging.basicConfig(level=self.level, filename=self.logfile)

    def read_temp_raw(self, device_file):
        lines = ""
        try:
            with open(device_file) as dfile:
                lines = dfile.readlines()
                dfile.close()
        except Exception, e:
            logging.ERROR("Exception while reading device file %s:%s" % (device_file, e))
        return lines

    def read_temp(self):
        for device, path in self.device_paths:
            lines = self.read_temp_raw(path)
            if lines[0].strip()[-3:] == 'YES':
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos+2:]
                    temp_c = float(temp_string) / 1000.0
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    logging.INFO("Device %s: %f %f" % (self.get_device_label(device), temp_c, temp_f))
                else:
                    logging.ERROR("Unable to find temperature in device %s in file %s" % (device, path))
            else:
                logging.WARN("Failed CRC on device %s" % self.get_device_label(device))

    def get_device_label(self, device):
        if device in self.device_labels:
            return self.device_labels[device]
        return device

    def run(self):
        while not self.stop.isSet():
            self.read_temp()
            time.sleep(1)

    def join(self, timeout=None):
        self.stop.set()
        super(ReadTemp, self).join(timeout)

    def read_config(self):
        if os.path.isfile(self.CONFIG_FILE):
            with open(self.CONFIG_FILE) as config_file:
                for line in config_file:
                    device, label = line.partition("=")[::2]
                    self.device_labels[device] = label
        else:
            logging.WARN("No config file present..using native device labels")


temp = ReadTemp()
temp.start()
time.sleep(10)
temp.join()
