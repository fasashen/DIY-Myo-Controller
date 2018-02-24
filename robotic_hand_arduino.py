import serial
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
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
    print('Synchronization is done.')
    return(A)

def realtime_emg(ard):
    packsize = 17
    numread = 20
    plotsize = 256
    frequency = 256
    k = 0

    syncbyte1 = 165
    syncbyte2 = 90

    # Voltage data of 6 channels
    data = [[0]*plotsize,
            [0]*plotsize,
            [0]*plotsize,
            [0]*plotsize,
            [0]*plotsize,
            [0]*plotsize]

    x_time = [x/frequency for x in range(plotsize)]

    storage_emg = []
    storage_volt = []

    plt.ion()

    fig = plt.figure()
    ax = fig.add_subplot(311)
    ax.set_xlim(0,1)
    # ax.set_ylim(450,550)
    ax.set_xlabel('Time')
    ax.set_ylabel("Voltage")
    ax.grid()
    ax.ticklabel_format(axis='both', style='plain')

    ch1, = ax.plot(x_time, data[0], '-b', label ='Channel 1', linewidth = 1)
    ch2, = ax.plot(x_time, data[1], '--r', label ='Channel 2', linewidth = 1)
    # ch3, = ax.plot(x_time, data[2], label ='Channel 3', linewidth = 1)
    ax.legend(loc='upper left')

    fig.show()

    while True:
        if ard.inWaiting() >= numread * packsize:
            for i in range(numread):

                A = struct.unpack('{}B'.format(packsize),ard.read(packsize))
                while syncbyte1 not in A and syncbyte2 not in A:
                    A = struct.unpack('{}B'.format(packsize),ard.read(packsize))
                if A[0] != syncbyte1 or A[1] != syncbyte2:
                    A = datasync(A,syncbyte1,syncbyte2,packsize)

                data[0][k] = typecast_swap_float(A[4:6]) # Channel 1 data
                data[1][k] = typecast_swap_float(A[6:8]) # Channel 2 data
                data[2][k] = typecast_swap_float(A[8:10]) # Channel 3 data

                # storage_emg.append(A[4:6]) # Storing Channel 1 history data for future debugging
                # storage_volt.append(data[0][k])

                k = k + 1
                if k >= plotsize:
                    # with open('emg_history.pickle', 'w b') as f:
                    #     pickle.dump([storage_emg, storage_volt], f, protocol=pickle.HIGHEST_PROTOCOL)
                    k = 1

        else:
            # print('Waiting for bytes from Arduino')
            pass


        ch1.set_ydata(data[0])
        ch2.set_ydata(data[1])
        # ch3.set_ydata(data[2])
        ax.relim()
        ax.autoscale_view()
        plt.pause(0.01)

        packets_inwaiting = int(np.round(ard.inWaiting()/packsize))
        if packets_inwaiting >= 30:
            print('Update rate is slow: {} packets inwaiting.'.format(packets_inwaiting))

    ard.close()
    print('Connection closed.')


ard = establish_connection('COM3')
if ard: realtime_emg(ard)

# with open('emg_history.pickle', 'rb') as f:
#     data = pickle.load(f)
