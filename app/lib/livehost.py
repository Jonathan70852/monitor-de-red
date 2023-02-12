import nmap
from scapy.all import *
import mysql.connector
from time import time
from lib.snmp import create_list, snmp_device_scan


def arp_scan(network):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=network, arguments='-sS')
    for host in scanner.all_hosts():
        print(host)
        if host != "192.168.0.1":
            conn=mysql.connector.connect(host="localhost", user="root", password="", db="net_cube")           
            cur = conn.cursor()
            cur.execute("DELETE FROM DISPOSITIVOS where IP='" + host + "'")
            varBinds = snmp_device_scan(comnty='public', hostip=host)
            #print(varBinds)
            if not varBinds is None:
                print(varBinds[4][1])
                cur.execute("INSERT INTO DISPOSITIVOS (IP, HOSTNAME) VALUES (%s, %s)", (host, str(varBinds[4][1])))
                conn.commit()
                conn.close()