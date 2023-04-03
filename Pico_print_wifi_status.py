#!/usr/bin/env python
# -*- coding: utf-8 -*-

import network

# main routine
if __name__ == "__main__":
    wifi = network.WLAN(network.STA_IF)
    print("{:2d}: IDLE".format(network.STAT_IDLE))
    print("{:2d}: CONNECTING: ".format(network.STAT_CONNECTING))
    print("{:2d}: GOT_IP".format(network.STAT_GOT_IP))
    print("{:2d}: CONNECT_FAIL".format(network.STAT_CONNECT_FAIL))
    print("{:2d}: NO_AP_FOUND".format(network.STAT_NO_AP_FOUND))
    print("{:2d}: WRONG_PASSWORD".format(network.STAT_WRONG_PASSWORD))
    
    