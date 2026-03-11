import machine
import time
import random
"""
Library for the Sensirion SEN66 multi-sensor module.

Hardware Connections:
 - VCC: 3.3 V (only 1 wire has to be connected)
 - Ground (only 1 wire has to be connected)
 - I2C: @100 kHz

Code is not yet compleet. Working with default settings and able to read out
measurement values
"""

class SEN66:
    address = 0x6b #107
    clean_interval_bounds= (86400,2*86400) # clean every other day the fan
    mode = 'idle'
    commands = {
                'activate_sht_heater': {'code': [0x67, 0x65], 'delay':20, 'length':0, 'mode': 'idle'},
                'device_reset':        {'code': [0xd3, 0x04], 'delay':1200, 'length':0, 'mode':'idle'},
                'get_ambient_pressure':{'code': [0x67, 0x20], 'delay':20, 'length':3, 'mode': 'both'}, 
                'get_data_ready':      {'code': [0x02, 0x02], 'delay':20, 'length':3, 'mode': 'measurement'},
                'get_product_name' :   {'code': [0xd0, 0x14], 'delay':20, 'length':48, 'mode': 'both'},
                'get_sensor_altitude': {'code': [0x67, 0x36], 'delay':20, 'length':3, 'mode': 'idle'}, 
                'get_serial_number':   {'code': [0xd0, 0x33], 'delay':20, 'length':48, 'mode': 'both'},
                'get_sht_heater_measurement':{'code':[0x67,0x90], 'delay':20, 'length':6, 'mode': 'idle'}, 
                'get_version':         {'code': [0xd1, 0x00], 'delay':20, 'length':12, 'mode':'both'},
                'start_fan_cleaning':  {'code': [0x56, 0x07], 'delay':20, 'length':0, 'mode': 'idle'},
                'start_measurement':   {'code': [0x00,0x21], 'delay':50, 'length':0, 'mode': 'idle'},
                'stop_measurement':    {'code': [0x01, 0x04], 'delay':1000, 'length':0, 'mode': 'measurement'},
                'read_and_clear_device_status': {'code': [0xd2, 0x10], 'delay':20, 'length':6, 'mode':'both'},
                'read_device_status':  {'code': [0xd2, 0x06], 'delay':20, 'length':6, 'mode':'both'},
                'read_measured_raw' :  {'code': [0x04, 0x05], 'delay':20, 'length':15, 'mode': 'measurement'},
                'read_measured_values':{'code': [0x03, 0x00], 'delay':20, 'length':27, 'mode':'measurement'},
                'read_number_concentration': {'code': [0x03, 0x16], 'delay':20, 'length':15, 'mode':'measurement'},
                }
    
    def __init__(self, i2c, address=None, wdt=None):
        """ 
        Initialize the Sensirion SEN66 sensor

        arguments:
           i2c: i2c object connected to the bus where the sensor is connected.
           address: (optional) I2C address of the sensor, default 0x6B
           wdt: (optional) watchdog-timer object with a feed argument. Will feed every other second orso.

        raises:
           raises an error if the sensor can not be detected on the I2C bus.
        """
        self.wdt = wdt
        self.i2c = i2c
        if address:
            self.address = address
        self.__I2C_scan()
        self.wdt_feed()
        self.get_id()
        self.clean_interval = random.randint(self.clean_interval_bounds[0], self.clean_interval_bounds[1])
        self.t0 = time.time()
        self.wdt_feed()
        
    def wdt_feed(self):
        """
        Feed the watchdog. 
        """
        if self.wdt:
            self.wdt.feed()
    
    def print_string(self, data):
        """ Creates a printable string from the data.

        arguments:
          data: list of bytes from the SEN66. Should be 2 bytes followed
                by one CRC byte. 
        return:
          data as string-object from the data where the CRC bytes are excluded.
          Zero's (0x00) add the end of the string are removed.
        """
        
        ll = sorted(list(range(0,len(data), 3))
                    + list(range(1, len(data), 3)))
        data = ''.join([chr(data[ii]) for ii in ll])
        return data.replace('\x00', '') # replace empties...
        
    def get_status(self, verbose=False):
        """ Get the status from the sensor
        Fills the status member of this object with the status bits (32 bit). 

        arguments:
          verbose: (default False) if true prints the status bits of the sensor
        """
        status = self.crc_all(self.__I2C_write('read_device_status'))
        if status is None:
            raise Exception('CRC error reading device status!')
        self.status = (status[0] << 24) + (status[1] << 16) + (status[3] << 8) + status[4]
        if verbose:
            print('Status bits:')
            print('{0:016b}'.format(self.status))
    
    def get_id(self, verbose=False):
        """ Get the product name, serial number and firmware version of the sensor

        arguments:
          verbose: (default = False) also print all the information.
        raises:
          Error: if SEN66 string is not found in the product name.
        """
        
        self.name = self.crc_all(self.__I2C_write('get_product_name'))
        if self.name:
            self.name = self.print_string(self.name)
        if self.name != 'SEN66':
            print(self.name)
            raise Exception('Something wrong with the sensorstring! Did you get an SEN66?')
        firmware = self.crc_all(self.__I2C_write('get_version'))
        if firmware is None:
            raise Exception('CRC error reading firmware version!')
        self.firmware = float("%d.%d" %(firmware[0], firmware[1]))
        serial_data = self.crc_all(self.__I2C_write('get_serial_number'))
        if serial_data is None:
            raise Exception('CRC error reading serial number!')
        self.serial = self.print_string(serial_data)
        if verbose:
            print('Sensor: ',self.name)
            print("Firmware version: %2.1f" %(self.firmware))
            print("Serial: ", self.serial)
            
    def crc_all(self, data):
        crc = 0
        for ii in range(len(data)//3):
            item = ii*3
            crc += self.__CRC([data[item], data[item+1]]) - data[item+2]
        if crc == 0:
            return data
        else:
            return None
            
    def start(self):
        self.__I2C_write('start_measurement')
        self.mode = 'measurement'
        
    def stop(self):
        self.__I2C_write('stop_measurement')
        self.mode = 'idle'
        
    def get_data(self):
        if self.mode != 'measurement':
            raise Exception('device not in measurement mode!')
        ready = self.__I2C_write('get_data_ready')
        data = None
        if ready[1] & 0x01:
            data = self.__I2C_write('read_measured_values')
            pm1p0 = self.parse_crc(data[0], data[1], data[2])
            pm2p5 = self.parse_crc(data[3], data[4], data[5])
            pm4p0 = self.parse_crc(data[6], data[7], data[8])
            pm10p0 = self.parse_crc(data[9], data[10], data[11])
            amb_hum = self.parse_crc(data[12], data[13], data[14])
            amb_temp = self.parse_crc(data[15], data[16], data[17])
            voc = self.parse_crc(data[18], data[19], data[20])
            nox = self.parse_crc(data[21], data[22], data[23])
            co2 = self.parse_crc(data[24], data[25], data[26])
            if None in (pm1p0, pm2p5, pm4p0, pm10p0, amb_hum, amb_temp, voc, nox, co2):
                return None
            pm1p0 = pm1p0 / 10
            pm2p5 = pm2p5 / 10
            pm4p0 = pm4p0 / 10
            pm10p0 = pm10p0 / 10
            amb_hum = amb_hum / 100
            amb_temp = amb_temp / 200
            voc = voc / 10
            nox = nox / 10
            data = (pm1p0, pm2p5, pm4p0, pm10p0, amb_hum, amb_temp, voc, nox, co2) 
        self.clean()
        return data
            
    def clean(self, force=False):
        now = time.time()
        self.wdt_feed()
        if force or ((now - self.t0) > self.clean_interval):
            print('cleaning fan!')
            # set new times
            self.clean_interval = random.randint(self.clean_interval_bounds[0], self.clean_interval_bounds[1])
            self.t0 = now
            # stop measurement, clean, and start gain
            self.__I2C_write('stop_measurement')
            self.wdt_feed()
            time.sleep(1)
            self.__I2C_write('start_fan_cleaning')
            for ii in range(5):
                self.wdt_feed()
                time.sleep(3)
            self.__I2C_write('start_measurement')
        
               
    def parse_crc(self, b1, b2, crc):
        if self.__CRC([b1, b2]) != crc:
            return None
        return (b1 << 8) + b2
    
    def __I2C_scan(self):
        self.wdt_feed()
        bus = self.i2c.scan()
        if (self.address not in bus):
            print(bus, self.address)
            raise OSError("device not found! Are the cables connected?")

    def __I2C_write(self, command):
        self.wdt_feed()
        self.i2c.writeto(self.address, bytearray(self.commands[command]['code']))
        time.sleep(self.commands[command]['delay']/1000)
        self.wdt_feed()
        data = None
        if self.commands[command]['length'] > 0:
            data = self.__I2C_read(command)
        return data
    
    def __I2C_read(self, command):
        return self.i2c.readfrom(self.address, self.commands[command]['length'])
        
        
    def __CRC(self, data):
        poly = 0x31
        init = 0xff
        crc = init
        for ii in range(len(data)):
            crc ^= (data[ii])
            crc &= 0xff
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ poly
                else:
                    crc = (crc << 1)
                crc &= 0xff
        return crc
    
if __name__ == "__main__":
    i2c0 = machine.SoftI2C(sda=machine.Pin(5), scl=machine.Pin(6), freq=100000)  # XIAO ESP32-S3: SDA=GPIO5, SCL=GPIO6
    sen = SEN66(i2c0)
    sen.start()
    sen.clean(force=True) # force a cleanup of the sensor
    #for ii in range(5):
    running = True
    while running:
        try:
            print(sen.get_data())
            time.sleep(1)
        except KeyboardInterrupt:
            running = False
    sen.stop()

    
