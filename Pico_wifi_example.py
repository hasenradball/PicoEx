#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import
import machine
import network
import rp2
import time


# WLAN-Konfiguration
config = {'ssid': 'default', 'key': 'default'}

# Status-LED
led_onboard = machine.Pin('LED', machine.Pin.OUT, value = 0)

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
        if not self.wlan.isconnected():
            return True
        print("\nWLAN disconnecting...")
        self.wlan.disconnect()
        while self.wlan.isconnected():
            time.sleep(0.1)
        print("WLAN disconnected!")
        led_onboard.off()
        return True
    
    def get_rssi(self):
        '''
        get the wifi strength in dB
        '''
        return self.wlan.status('rssi')


# main routine
if __name__ == "__main__":
    wifi = Wlan()
    try:
        wifi.connect(config)
        #print("RSSI: ", wifi.get_rssi())
        pass
    
    except Exception as err:
        print("Error: ", err)        
        pass

    else:
        print("else path...")
        
        
    finally:
        time.sleep(10)
        wifi.disconnect()