import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
import time
import struct

def establish_connection(serialport='/dev/cu.wchusbserial1420',baudrate=115200):
    try:
        arduino = serial.Serial(serialport, baudrate)
    except:
        print('Could not find serial port')

    time_elapsed = 0
    timeout = 5
    connection_established = False
    first_byte = None

    t = time.time()
    while time_elapsed < timeout:

        time_elapsed = time.time() - t

        if arduino.inWaiting():
            first_byte = arduino.read()

        if first_byte == b'A':
            arduino.write(b'h')
            connection_established = True
            time_elapsed = timeout + 1

    if connection_established:
        print('Connection established in {} seconds.'.format(np.round(time.time() - t, 2)))
        return arduino
    else:
        print('Connection failed.')
        arduino.close()
        return None


def realtime_emg(ard):
    if ard:
        packsize = 17
        numread = 20
        k = 0
        data = []

        plt.ion()
        plt.ylabel('Voltage')
        plt.xlabel('Ts')
        plt.axis([0, 256,-10,260])


        while True:
            if ard.inWaiting() >= numread * packsize:
                for i in range(numread):
                    # A = struct.unpack('{}B'.format(packsize),ard.read(packsize))
                    A = ard.read(packsize)
                    # A = np.array(br,dtype=np.uint8)
                    print(A.decode('utf-8', 'ignore'))
                    # data.append(abs(A[5]-A[4]))

                    k = k + 1
                    # plt.plot(range(len(data)), data)
                    # plt.pause(0.05)

                if k >= 1:
                    k = 0
                    break


        ard.close()
        print('Connection closed.')


ard = establish_connection()
realtime_emg(ard)
