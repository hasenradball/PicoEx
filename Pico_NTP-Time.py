# Bibliotheken laden
import machine
import network
import rp2
import sys
import utime as time
import usocket as socket
import ustruct as struct

# WLAN-Konfiguration
config = {'ssid': 'your ssid', 'key': 'your password'}

# Status-LED
led_onboard = machine.Pin('LED', machine.Pin.OUT, value = 0)

# NTP-Host
NTP_HOST = 'ptbtime3.ptb.de'

class Wlan():

    def __init__(self):
        '''
        constructor
        '''
        self.wlan = network.WLAN(network.STA_IF)
        rp2.country('DE')
        # Remark:
        #  0 - STAT_IDLE – no connection and no activity
        #  1 - STAT_CONNECTING – connecting in progress
        #  3 - STAT_GOT_IP
        # -1 - STAT_CONNECT_FAIL – failed due to other problems
        # -2 - STAT_NO_AP_FOUND – failed because no access point replied
        # -3 - STAT_WRONG_PASSWORD – failed due to incorrect password
        self.status = {
            network.STAT_CONNECTING: 'STAT_CONNECTING',
            network.STAT_CONNECT_FAIL: 'STAT_CONNECT_FAIL',
            network.STAT_GOT_IP: 'STAT_GOT_IP',
            network.STAT_IDLE: 'STAT_IDLE',
            network.STAT_NO_AP_FOUND: 'STAT_NO_AP_FOUND',
            network.STAT_WRONG_PASSWORD: 'STAT_WRONG_PASSWORD'
        }
    
    def connect(self, config):
        '''
        connect wlan method
        '''
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print('WLAN-Verbindung herstellen')
            self.wlan.connect(**config)
            for i in range(10):
                if (self.wlan.status() < 0) or (self.wlan.status() == network.STAT_GOT_IP):
                    break
                led_onboard.toggle()
                print('.', end = "")
                time.sleep(1)
        if self.wlan.isconnected():
            print('\nWLAN-Verbindung hergestellt / WLAN-Status:', self.status[self.wlan.status()])
            print("IFconfig: ", self.wlan.ifconfig())
            led_onboard.on()
            return True
        else:
            print('\nKeine WLAN-Verbindung')
            led_onboard.off()
            print('WLAN-Status:', self.status[self.wlan.status()])
            return False

    def disconnect(self):
        '''
        disconnect wlan method
        '''
        print("\nWLAN disconecting...")
        self.wlan.disconnect()
        while self.wlan.isconnected():
            time.sleep(0.1)
        print("WLAN disconected!")
	led_onboard.off()
        return True

class Pico_MESZ():
    '''
    Class for Pi Pico W which gets the NTP Time from time server
    and updates the RTC of the Pi Pico
    '''

    def __init__(self, ntp_host, tz_offset = 1):
        # check if RTC uses 2000 or 1970 epoch
        self.NTP_DELTA = 3155673600 if time.gmtime(0)[0] == 2000 else 2208988800
        # define weekday
        self.wday = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
        self._calc_year = 0
        self.ntp_server = ntp_host
        self.tz = tz_offset
        
    def isSummerTime(self, tm):
        '''
        calulate if it is Summer time
        Remark: time struct tm = (year, month, mday, hour, minute, second, weekday, yearday)
        '''
        year = tm[0]
        month = tm[1]
        mday = tm[2]
        hour = tm[3]
        # keine Sommerzeit zwischen November und Februar
        if (month < 3 or month > 10): return False
        # Sommerzeit zwischen April und September
        if (month > 3 and month < 10): return True
        # Berechnung der Sommerzeit im März und Oktober
        if (year != self._calc_year):
            self._calc_year = year
            
            # Berechne die Stunden zum Zeitpunkt der Umstellung im März
            # Die Sommerzeit beginnt immer am letzten Sonntag im März
            self._t1 = 24 * (31 - (5 * self._calc_year / 4 + 4) % 7) + 1
            
            # Berechne die Stunden zum Zeitpunkt der Umstellung im Oktober
            # Die Winterzeit beginnt immer am letzten Sonntag im Oktober
            self._t2 = 24 * (31 - (5 * self._calc_year / 4 + 1) % 7) + 1
        
        Anz_Std = hour + 24 * mday
        # Wenn März und Std >= Zeitpunkt der Umstellung --> Sommerzeit
        if (month == 3 and Anz_Std >= self._t1): return True
        # Wenn Oktober und Std < Zeitpunkt der Umstellung --> Sommerzeit
        if (month == 10 and Anz_Std < self._t2): return True
        return False

    
    def getMESZ(self):
        '''
        a) get the time from NTP Server based on 1.1.1900 00:00:00
        b) calculate the UNIX time (1.1.1970 00:00:00)
        c) and return the struct tm based on local time with respect of DST
        '''
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(self.ntp_server, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(3)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        except OSError as err:
            print("OS error get MESZ():", err)
        finally:
            s.close()
        # get NTP timestamp since 1900
        ntp_time = struct.unpack("!I", msg[40:44])[0]
        # calc unix timestamp since 1970
        unix_time = ntp_time - self.NTP_DELTA
        # time struct tm = (year, month, mday, hour, minute, second, weekday, yearday)
        tm = time.gmtime(unix_time)
        # now check if it is summer time
        local_time = unix_time + self.tz * 3600
        if self.isSummerTime(tm):
            print("DST: 1")
            local_time += 3600
        else:
            print("DST: 0")
        return time.gmtime(local_time)
    
    def setTime_RTC(self):
        '''
        set the time to RTC
        '''
        # localtime => (year, month, mday, hour, minute, second, weekday, yearday)
        (YY, MM, DD, hh, mm, ss, wday, yday) = self.getMESZ()
        
        # datetime => (year, month, mday, weekday, hour, minute, second, subsecond)
        machine.RTC().datetime((YY, MM, DD,  wday + 1, hh, mm, ss, 0))

    def getTime_RTC(self):
        '''
        get the time from rtc
        '''
        return machine.RTC().datetime()
    
    def showTime(self):
        '''
        show the actual MESZ time
        '''
        #datetime() => (year, month, day, weekday, hours, minutes, seconds, subseconds)
        (year, month, day, weekday, hours, minutes, seconds, subseconds) = machine.RTC().datetime()
        print("MESZ: {} {:02d}.{:02d}.{} - {:02d}:{:02d}:{:02d}".format(self.wday[weekday], day, month, year, hours, minutes, seconds))
        
        

# main routine
if __name__ == "__main__":
    try:
        wifi = Wlan()
        rtc = Pico_MESZ(NTP_HOST)
        
        # WLAN-Verbindung herstellen
        if wifi.connect(config):
            # Zeit setzen
            rtc.setTime_RTC()
            pass

        # hole Datum aus der RTC
        print("\ntime from rtc:", machine.RTC().datetime())
        rtc.showTime()
    
    except OSError as err:
        print("OS error in main:", err)
    
    finally:
        wifi.disconnect()
    