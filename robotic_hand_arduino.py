import serial
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import struct
import pickle


def establish_connection(serialport='/dev/cu.wchusbserial1420',baudrate=115200):
    try:
        arduino = serial.Serial(serialport, baudrate)
    except:
        print('Could not find serial port')
        return False

    time_elapsed = 0
    timeout = 5
    connection_established = False
    first_byte = None

    t = time.time()
    while time_elapsed < timeout:

        time_elapsed = time.time() - t

        if arduino.inWaiting():
            first_byte = arduino.read(1)

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

def datasync(A,syncbyte1,syncbyte2,packsize):
    sb1_index = A.index(syncbyte1)
    if A[sb1_index + 1] == syncbyte2:
        sb2_index = sb1_index + 1
    else:
        sb1_index = A[sb1_index+1:].index(syncbyte1) + sb1_index + 1
        sb2_index = sb1_index + 1

    if sb2_index >= packsize: sb2_index = 0

    B = struct.unpack('{}B'.format(sb1_index),ard.read(sb1_index))
    A = A[sb1_index:] + B
    return(A)


def realtime_emg(ard):
    packsize = 17
    numread = 20
    plotsize = 256
    k = 0

    syncbyte1 = 165
    syncbyte2 = 90

    data = [[0]*plotsize,
            [0]*plotsize,
            [0]*plotsize]

    storage_emg = []
    storage_volt = []

    plt.ion()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlim(0,plotsize)
    ax.set_ylim(450,550)
    ax.set_

    ch1, = ax.plot(range(plotsize), data[0], label ='Channel 1', linewidth = 1)
    ch2, = ax.plot(range(plotsize), data[1], label ='Channel 2', linewidth = 1)
    ch3, = ax.plot(range(plotsize), data[2], label ='Channel 3', linewidth = 1)

    fig.show()

    while True:
        if ard.inWaiting() >= numread * packsize:
            for i in range(numread):

                A = struct.unpack('{}B'.format(packsize),ard.read(packsize))
                while syncbyte1 not in A and syncbyte2 not in A:
                    A = struct.unpack('{}B'.format(packsize),ard.read(packsize))

                print(A)
                if A[0] != syncbyte1 or A[1] != syncbyte2:
                    A = datasync(A,syncbyte1,syncbyte2,packsize)

                data[0][k] = typecast_swap_float(A[4:6]) # Channel 1 data
                data[1][k] = typecast_swap_float(A[6:8]) # Channel 2 data
                data[2][k] = typecast_swap_float(A[8:10]) # Channel 3 data

                # storage_emg.append(A[4:6]) # Storing Channel 1 history data for future debugging
                # storage_volt.append(data[0][k])

                k = k + 1
                if k >= plotsize:
                    # with open('emg_history.pickle', 'wb') as f:
                    #     pickle.dump([storage_emg, storage_volt], f, protocol=pickle.HIGHEST_PROTOCOL)
                    # plt.savefig('test.png')
                    k = 1

        else:
            print('Waiting for bytes from Arduino')


        ch1.set_ydata(data[0])
        ch2.set_ydata(data[1])
        ch3.set_ydata(data[2])
        # fig.canvas.draw()
        plt.pause(1/1152000)

        packets_inwaiting = np.round(ard.inWaiting()/packsize)
        print(packets_inwaiting)
        if packets_inwaiting >= 30:
            print('Update rate is too slow: {}'.format(packets_inwaiting))

    ard.close()
    print('Connection closed.')



ard = establish_connection('COM3')
if ard: realtime_emg(ard)

# A = (165, 90) + (2, 24, 2, 2, 2, 4, 2, 2, 1, 238, 1, 220, 1, 208, 1)
# print(A[2:])

# with open('emg_history.pickle', 'rb') as f:
#     data = pickle.load(f)
#
# for b,v in zip(data[0],data[1]):
#     print(b,typecast_swap_float(b))
