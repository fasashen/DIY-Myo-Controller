import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
import time
import struct
import pickle

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

def typecast_swap_float(arr):
    '''
    Magicaly converts uint8 array to uint16 value and swap bytes.
    Replica of Matlab typecast() and swapbytes() functions
    Returns float value
    '''
    arr = np.flip(np.uint8(arr),0)
    result = float(np.uint16(arr[1]/255*65535-arr[1]+arr[0]))
    return result

def realtime_emg(ard):
    if ard:
        packsize = 17
        numread = 20
        plotsize = 256
        k = 0

        data = [[0]*plotsize,
                [0]*plotsize,
                [0]*plotsize]

        plt.ion()
        plt.ylabel('Voltage')
        plt.xlabel('Ts')

        while True:
            if ard.inWaiting() >= numread * packsize:
                for i in range(numread):
                    try:
                        A = struct.unpack('{}B'.format(packsize),ard.read(packsize))
                    except:
                        ard.close()
                    data[0][k] = typecast_swap_float(A[4:6]) # Channel 1 data
                    data[1][k] = typecast_swap_float(A[6:8]) # Channel 2 data
                    data[2][k] = typecast_swap_float(A[8:10])

                    plt.plot(range(plotsize), data[0])
                    plt.plot(range(plotsize), data[1])
                    plt.plot(range(plotsize), data[2])
                    plt.pause(0.05)


                    k = k + 1
                    if k >= plotsize:
                        k = 1



        with open('emg_binary_data.pickle', 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        ard.close()
        print('Connection closed.')



ard = establish_connection()
realtime_emg(ard)

# with open('emg_binary_data.pickle', 'rb') as f:
#     data = pickle.load(f)
#
# print(data)
