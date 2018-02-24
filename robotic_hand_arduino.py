import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
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
    arr = np.uint8(arr)
    if arr[0] < arr[1]:
        arr = np.flip(arr,0)
    result = float(np.uint16(arr[1]/255*65535-arr[1]+arr[0]))
    return result

def realtime_emg(ard):
    packsize = 17
    numread = 20
    plotsize = 256
    k = 0

    data = [[0]*plotsize,
            [0]*plotsize,
            [0]*plotsize]

    storage_emg = []
    storage_volt = []

    plt.ion()

    fig = plt.figure()
    ax = fig.add_subplot(111)


    ax.plot(range(plotsize), data[0], label ='Channel 1')
    ax.plot(range(plotsize), data[1], label ='Channel 2')
    ax.plot(range(plotsize), data[2], label ='Channel 3')

    fig.show()

    while True:
        if ard.inWaiting() >= numread * packsize:
            for i in range(numread):
                A = struct.unpack('{}B'.format(packsize),ard.read(packsize))

                data[0][k] = typecast_swap_float(A[4:6]) # Channel 1 data
                data[1][k] = typecast_swap_float(A[6:8]) # Channel 2 data
                data[2][k] = typecast_swap_float(A[8:10]) # Channel 3 data

                storage_emg.append(A[4:6]) # Storing Channel 1 history data for future debugging
                storage_volt.append(data[0][k])

                ax.clear()
                ax.set_xlim(0,plotsize)
                ax.plot(range(plotsize), data[0], linewidth = 0.5, label = 'Channel 1')
                ax.plot(range(plotsize), data[1], linewidth = 0.5, label = 'Channel 2')
                ax.plot(range(plotsize), data[2], linewidth = 0.5, label = 'Channel 3')
                plt.pause(0.05)

                k = k + 1
                if k >= plotsize:
                    with open('emg_history.pickle', 'wb') as f:
                        pickle.dump([storage_emg, storage_volt], f, protocol=pickle.HIGHEST_PROTOCOL)
                    k = 1

    ard.close()
    print('Connection closed.')



# ard = establish_connection()
# if ard: realtime_emg(ard)

with open('emg_history.pickle', 'rb') as f:
    data = pickle.load(f)

for b,v in zip(data[0],data[1]):
    print(b,typecast_swap_float(b))

# A = (2, 1)
# B = typecast_swap_float(A)
# print(A,B)
