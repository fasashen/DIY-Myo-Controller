import serial
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
import struct
import pickle
from scipy import signal

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
            print('Serial port found. Trying to establish connection...')
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
        '''
        Resolve serial data flow desync,
        which tend to be a common problem on Mac only (don't know why)
        '''
        print(A)
        sb1_index = A.index(self.syncbyte1)
        sb2_index = A.index(self.syncbyte2)
        B = struct.unpack('{}B'.format(sb1_index),self.arduino.read(sb1_index))
        A = A[sb1_index:] + B
        print(A)
        print('Synchronization is done.')
        return(A)

    def realtime_emg(self):
        '''
        Realtime reading and processing of data from Arduino electrodes
        '''
        plotsize = self.frequency
        nstd_timespan = 10 # 10 second
        plotsize_nstd = nstd_timespan*self.numread

        k = 0
        k_nstd = 0

        # Voltage data of 6 channels
        data = [[0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize]
        x_time = [x/self.frequency for x in range(plotsize)]

        # Fourie transform of voltage data for Channel 1
        nfft = self.frequency
        ft_x = [int(self.frequency/nfft*x) for x in range(int(nfft/2))]
        ft0_data = [[0]*nfft]
        ft_data = [[0]*len(ft_x)]

        # Standard deviation of 6 channels
        nanstd_data = [[0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd]

        # Trying to pick up rigth time scale (doesn't work properly, redesign is needed)
        nstd_time = [x/np.round(self.frequency/self.numread) for x in range(plotsize_nstd)]

        storage_emg = []
        storage_volt = []

        # plt.ion()
        fig = plt.figure()

        # Voltage channels plot
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

        # Fourie transform plot
        ftplot = fig.add_subplot(312)
        ftplot.set_xlim(0,128)
        ftplot.set_title('Fourie transform')
        ftplot.set_xlabel('Freq')
        ftplot.set_ylabel('Power')
        ftplot.grid()
        ftplot.ticklabel_format(axis='both', style='plain')
        ft1, = ftplot.plot(ft_x, ft_data[0], '-b', label ='Channel 1', linewidth = 0.5)

        # Standard deviation of voltage plot
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

                    # Reads and converts input binary data to uint8
                    A = struct.unpack('{}B'.format(self.packsize),self.arduino.read(self.packsize))

                    # Checks if what we just read is valid data, if desync resolve it
                    while True:
                        if self.syncbyte1 in A and self.syncbyte2 in A:
                            break
                        A = struct.unpack('{}B'.format(self.packsize),self.arduino.read(self.packsize))
                    if A[0] != self.syncbyte1 or A[1] != self.syncbyte2:
                        A = self.datasync(A)

                    # Converts uint8 data to float
                    data[0][k] = self.typecast_swap_float(A[4:6]) # Channel 1 data
                    data[1][k] = self.typecast_swap_float(A[6:8]) # Channel 2 data
                    data[2][k] = self.typecast_swap_float(A[8:10]) # Channel 3 data

                    # storage_emg.append(A[4:6]) # Storing Channel 1 history data for future debugging
                    # storage_volt.append(data[0][k])

                    # Loops the plot
                    k += 1
                    if k >= plotsize:
                        k = 0


            # Fourie transform
            ft0_data[0] = np.fft.fft(data[0],nfft)
            ft_data[0] = [10*np.log10(abs(x)**2/self.frequency/plotsize) for x in ft0_data[0][0:int(nfft/2)]]

            # Standard deviation
            nanstd_data[0][k_nstd] = np.nanstd(data[0])
            nanstd_data[1][k_nstd] = np.nanstd(data[1])
            nanstd_data[2][k_nstd] = np.nanstd(data[2])

            # Loops the plot
            k_nstd += 1
            if k_nstd >= plotsize_nstd:
                k_nstd = 0

            # Send all new data to plot
            ch1.set_ydata(data[0])
            ch2.set_ydata(data[1])
            ch3.set_ydata(data[2])
            ax.relim()
            ax.autoscale_view()

            ft1.set_ydata(ft_data[0])
            ftplot.relim()
            ftplot.autoscale_view()

            ch1_nstd.set_ydata(nanstd_data[0])
            ch2_nstd.set_ydata(nanstd_data[1])
            ch3_nstd.set_ydata(nanstd_data[2])
            nstdplot.relim()
            nstdplot.autoscale_view()

            # Catches error when plot is closed by user
            try:
                plt.pause(0.0001)
            except:
                break

            # Checks if there are too many packets left in serial, e.g. if speed of processing is fast enough
            packets_inwaiting = int(np.round(self.arduino.inWaiting()/self.packsize))
            if packets_inwaiting >= 50:
                print('Update rate is slow: {} packets inwaiting, {} second delay.'.format(packets_inwaiting, np.round(packets_inwaiting/256,2)))

            # with open('emg_history.pickle', 'w b') as f:
            #     pickle.dump([storage_emg, storage_volt], f, protocol=pickle.HIGHEST_PROTOCOL)

        self.arduino.close()
        print('Connection closed.')


emg = EMG('COM3')
arduino = emg.establish_connection()
if arduino: emg.realtime_emg()
