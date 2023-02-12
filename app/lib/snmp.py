from pysnmp.hlapi import *
import netaddr


def snmp_device_scan(comnty, hostip, ):
    existsError = False
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(comnty, mpModel=0),
               UdpTransportTarget((hostip, 161), timeout=1, retries=0),
               ContextData(),
                ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')),#Dispositivo
               ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),#Descripcion
               ObjectType(ObjectIdentity('1.3.6.1.2.1.25.1.1.0')),#Tiempo conexion
               ObjectType(ObjectIdentity('1.3.6.1.2.1.1.6.0')),#Grupo red
               ObjectType(ObjectIdentity('1.3.6.1.2.1.1.4.0')),#Contacto
               ObjectType(ObjectIdentity('1.3.6.1.2.1.1.2.0')),#OID
               ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2.16')),#Adaptador de red
               ObjectType(ObjectIdentity('1.3.6.1.2.1.25.2.2.0')),#RAM
               ObjectType(ObjectIdentity('1.3.6.1.2.1.25.2.3.1.5.1')),#HDD Total
               ObjectType(ObjectIdentity('1.3.6.1.2.1.25.2.3.1.6.1')),#HDD Usado
               ObjectType(ObjectIdentity('1.3.6.1.2.1.25.2.3.1.3.1')),#Particion
               ObjectType(ObjectIdentity('1.3.6.1.2.1.25.2.3.1.3.2')),#Particion
               ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.6.17')),#MAC
               ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.15.8')),#Mbps/Ethernet
               ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.15.13'))#Mbps/wifi
               )
    )

    if errorIndication:
        print (errorIndication)
            
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            return varBinds


def create_list(ip):
    print("RECEIVED:" +ip)
    mgmt_ip_list = []
    snmp_scanrange = netaddr.IPNetwork(ip)
    for ip in snmp_scanrange.iter_hosts():
        mgmt_ip_list.append(ip)

    snmpwalk_data = []
    for mgmtIP in mgmt_ip_list:
        # print str(mgmtIP)
        try:
            snmp_raw_data = snmp_device_scan(comnty='public', hostip=str(mgmtIP))
            snmpscandata = {'Dispositivo': str(snmp_raw_data[0][1]),
                         'Sistema': str(snmp_raw_data[1][1]),
                         'Tiempo_conexion': str(snmp_raw_data[2][1]),
                         'Grupo_red': str(snmp_raw_data[3][1]),
                         'Contacto': str(snmp_raw_data[4][1]),
                         'OID' : str(snmp_raw_data[5][1]),
                         'Tarjeta_red' : str(snmp_raw_data[6][1]),
                         'RAM' : str(snmp_raw_data[7][1]),
                         'HDD Total' : str(snmp_raw_data[8][1]),
                         'HDD Usado' : str(snmp_raw_data[9][1]),
                         'Particiones' : str(snmp_raw_data[10][1] + " ; " +str(snmp_raw_data[11][1])),
                         'MAC' : str(snmp_raw_data[12][1]),
                         'IP': str(mgmtIP),
                         'Mbps_Ethernet': str(snmp_raw_data[13][1]),
                         'Mbps_wifi': str(snmp_raw_data[14][1]),
                         }
            snmpwalk_data.append(snmpscandata)
        except:
            print ('snmp scan error %s' % str(mgmtIP))

    lista=list(snmpwalk_data)
    print (lista)
    return lista

