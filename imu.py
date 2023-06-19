import serial
import struct
import time
import numpy as np


connected = False
port = '/dev/ttyUSB0'
baud = 115200


def get_angle(data):
    if len(data) < 7:
        print("BOO")
        return
    cmd = struct.unpack('c', data[0:1])[0]
    #print(cmd)
    if cmd == b'S': # 0x53
        return np.array(struct.unpack('<hhh', data[1:7]))/32768.0*180.0 
    return None



with serial.Serial(port,baud,timeout=5) as ser:
    s = ser.read()

    msg_num = 0
    while msg_num < 1000:
        start = time.time()
        s = ser.read_until(b'U')
        q = get_angle(s)
        if q is not None:
            msg_num = msg_num+1
            print(q[0])