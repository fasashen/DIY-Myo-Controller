import serial
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
import struct
import pickle

class EMG:
    def __init__(self, serialport='/dev/cu.wchusbserial1420',baudrate=115200,numread=20,packsize=17,frequency=256,syncbyte1=165,syncbyte2=90,connection_timeout=5,first_byte = b'A'):
        self.serialport = serialport
        self.baudrate = baudrate
        self.numread = numread
        self.packsize = packsize
        self.frequency = frequency
        self.syncbyte1 = syncbyte1
        self.syncbyte2 = syncbyte2
        self.timeout = connection_timeout
        self.first_byte = first_byte
        self.arduino = None

    def establish_connection(self):
        try:
            self.arduino = serial.Serial(self.serialport, self.baudrate)
        except:
            print('Could not find serial port')
            return None

        time_elapsed = 0
        connection_established = False
        first_byte = None

        t = time.time()
        while time_elapsed < self.timeout:

            time_elapsed = time.time() - t

            if self.arduino.inWaiting():
                first_byte = self.arduino.read(1)

            if first_byte == self.first_byte:
                self.arduino.write(b'h')
                connection_established = True
                time_elapsed = self.timeout + 1

        if connection_established:
            print('Connection established in {} seconds.'.format(np.round(time.time() - t, 2)))
            return self.arduino
        else:
            print('Connection failed.')
            self.arduino.close()
            return None

    def typecast_swap_float(self, arr):
        '''
        Magicaly converts uint8 array to uint16 value and swap bytes.
        Replica of Matlab typecast() and swapbytes() functions
        Returns float value
        '''
        arr = np.flip(np.uint8(arr),0)
        result = float(np.uint16(arr[1]/255*65535-arr[1]+arr[0]))
        return result

    def datasync(self, A):
        sb1_index = A.index(self.syncbyte1)
        if A[sb1_index + 1] == self.syncbyte2:
            sb2_index = sb1_index + 1
        else:
            sb1_index = A[sb1_index+1:].index(self.syncbyte1) + sb1_index + 1
            sb2_index = sb1_index + 1

        if sb2_index >= self.packsize: sb2_index = 0

        B = struct.unpack('{}B'.format(sb1_index),ard.read(sb1_index))
        A = A[sb1_index:] + B
        print('Synchronization is done.')
        return(A)

    def realtime_emg(self):

        plotsize = self.frequency
        plotsize_nstd = self.frequency*5 # 5 seconds plot width
        k = 0
        k_nstd = 0


        # Voltage data of 6 channels
        data = [[0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize]

        nanstd_data = [[0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd]

        x_time = [x/self.frequency for x in range(plotsize)]
        nstd_time = [x/self.frequency for x in range(plotsize_nstd)]

        storage_emg = []
        storage_volt = []

        # plt.ion()
        fig = plt.figure()

        ax = fig.add_subplot(311)
        ax.set_xlim(0,1)
        ax.set_xlabel('Time')
        ax.set_ylabel("Voltage")
        ax.grid()
        ax.ticklabel_format(axis='both', style='plain')

        ch1, = ax.plot(x_time, data[0], '-b', label ='Channel 1', linewidth = 0.5)
        ch2, = ax.plot(x_time, data[1], '--r', label ='Channel 2', linewidth = 0.5)
        ch3, = ax.plot(x_time, data[2], '--g', label ='Channel 3', linewidth = 0.5)
        ax.legend(loc='upper left')

        nstdplot = fig.add_subplot(313)
        nstdplot.grid()
        nstdplot.set_xlabel('Time, sec')
        nstdplot.set_ylabel('Standard deviation of Voltage')

        ch1_nstd, = nstdplot.plot(nstd_time, nanstd_data[0], '-b', label ='Channel 1', linewidth = 0.5)
        ch2_nstd, = nstdplot.plot(nstd_time, nanstd_data[1], '-r', label ='Channel 2', linewidth = 0.5)
        ch3_nstd, = nstdplot.plot(nstd_time, nanstd_data[2], '-g', label ='Channel 3', linewidth = 0.5)

        nstdplot.legend(loc='upper left')

        fig.show()

        while True:
            if self.arduino.inWaiting() >= self.numread * self.packsize:
                for i in range(self.numread):

                    A = struct.unpack('{}B'.format(self.packsize),self.arduino.read(self.packsize))
                    while self.syncbyte1 not in A and self.syncbyte2 not in A:
                        A = struct.unpack('{}B'.format(self.packsize),self.arduino.read(self.packsize))
                    if A[0] != self.syncbyte1 or A[1] != self.syncbyte2:
                        A = self.datasync(A)

                    data[0][k] = self.typecast_swap_float(A[4:6]) # Channel 1 data
                    data[1][k] = self.typecast_swap_float(A[6:8]) # Channel 2 data
                    data[2][k] = self.typecast_swap_float(A[8:10]) # Channel 3 data

                    # storage_emg.append(A[4:6]) # Storing Channel 1 history data for future debugging
                    # storage_volt.append(data[0][k])

                    nanstd_data[0][k_nstd] = np.nanstd(data[0])
                    nanstd_data[1][k_nstd] = np.nanstd(data[1])
                    nanstd_data[2][k_nstd] = np.nanstd(data[2])

                    k = k + 1
                    k_nstd = k_nstd + 1
                    if k >= plotsize:
                        k = 0
                    if k_nstd >= plotsize_nstd:
                        k_nstd = 0
            else:
                # print('Waiting for bytes from Arduino')
                pass

            ch1.set_ydata(data[0])
            ch2.set_ydata(data[1])
            ch3.set_ydata(data[2])
            ax.relim()
            ax.autoscale_view()

            ch1_nstd.set_ydata(nanstd_data[0])
            ch2_nstd.set_ydata(nanstd_data[1])
            ch3_nstd.set_ydata(nanstd_data[2])
            nstdplot.relim()
            nstdplot.autoscale_view()

            try: #Catches error when plot is closed by user
                plt.pause(0.0001)
            except:
                break

            packets_inwaiting = int(np.round(self.arduino.inWaiting()/self.packsize))
            if packets_inwaiting >= 50:
                print('Update rate is slow: {} packets inwaiting, {} second delay.'.format(packets_inwaiting, np.round(packets_inwaiting/256,2)))

            # with open('emg_history.pickle', 'w b') as f:
            #     pickle.dump([storage_emg, storage_volt], f, protocol=pickle.HIGHEST_PROTOCOL)

        self.arduino.close()
        print('Connection closed.')


emg = EMG('COM3')
arduino = emg.establish_connection()
emg.realtime_emg()
