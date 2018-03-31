import serial
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import time
import struct
import pickle
from scipy import signal
from multiprocessing import Process

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
        self.data = [[0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize,
                [0]*plotsize]
        self.x_time = [x/self.frequency for x in range(plotsize)]

        # Fourie transform of voltage data for Channel 1
        self.nfft = self.frequency
        self.ft_x = [int(self.frequency/self.nfft*x) for x in range(int(self.nfft/2))]
        self.ft0_data = [[0]*self.nfft]
        self.ft_data = [[0]*len(self.ft_x)]

        # Standard deviation of 6 channels
        self.nstd_data = [[0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd,
                       [0]*plotsize_nstd]

        # Trying to pick up rigth time scale (doesn't work properly, redesign is needed)
        self.nstd_time = [x/np.round(self.frequency/self.numread) for x in range(plotsize_nstd)]

        storage_emg = []
        storage_volt = []

        # Plot initialization
        self.plot_init()

        p = Process(target=self.plot_update())


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
                    self.data[0][k] = self.typecast_swap_float(A[4:6]) # Channel 1 data
                    self.data[1][k] = self.typecast_swap_float(A[6:8]) # Channel 2 data
                    self.data[2][k] = self.typecast_swap_float(A[8:10]) # Channel 3 data

                    # storage_emg.append(A[4:6]) # Storing Channel 1 history data for future debugging
                    # storage_volt.append(data[0][k])

                    # Loops the plot
                    k += 1
                    if k >= plotsize:
                        k = 0

            # Fourie transform
            self.ft0_data[0] = np.fft.fft(self.data[0],self.nfft)
            self.ft_data[0] = [10*np.log10(abs(x)**2/self.frequency/plotsize) for x in self.ft0_data[0][0:int(self.nfft/2)]]

            # Standard deviation
            self.nstd_data[0][k_nstd] = np.nanstd(self.data[0])
            self.nstd_data[1][k_nstd] = np.nanstd(self.data[1])
            self.nstd_data[2][k_nstd] = np.nanstd(self.data[2])

            # Loops the plot
            k_nstd += 1
            if k_nstd >= plotsize_nstd:
                k_nstd = 0


            self.plot_update()


            # Catches error when plot is closed by user
            try:
                plt.pause(0.0001)
            except:
                break

        self.arduino.close()
        print('Connection closed.')


    def plot_init(self):
        self.fig = plt.figure()

        # Voltage channels plot
        self.ax = self.fig.add_subplot(311)
        self.ax.set_xlim(0,1)
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel("Voltage")
        self.ax.grid()
        self.ax.ticklabel_format(axis='both', style='plain')

        self.ch1, = self.ax.plot(self.x_time, self.data[0], '-b', label ='Channel 1', linewidth = 0.5)
        self.ch2, = self.ax.plot(self.x_time, self.data[1], '--r', label ='Channel 2', linewidth = 0.5)
        self.ch3, = self.ax.plot(self.x_time, self.data[2], '--g', label ='Channel 3', linewidth = 0.5)
        self.ax.legend(loc='upper left')

        # Fourie transform plot
        self.ftplot = self.fig.add_subplot(312)
        self.ftplot.set_xlim(0,128)
        self.ftplot.set_title('Fourie transform')
        self.ftplot.set_xlabel('Freq')
        self.ftplot.set_ylabel('Power')
        self.ftplot.grid()
        self.ftplot.ticklabel_format(axis='both', style='plain')
        self.ft1, = self.ftplot.plot(self.ft_x, self.ft_data[0], '-b', label ='Channel 1', linewidth = 0.5)

        # Standard deviation of voltage plot
        self.nstdplot = self.fig.add_subplot(313)
        self.nstdplot.grid()
        self.nstdplot.set_xlabel('Time, sec')
        self.nstdplot.set_ylabel('Standard deviation of Voltage')

        self.ch1_nstd, = self.nstdplot.plot(self.nstd_time, self.nstd_data[0], '-b', label ='Channel 1', linewidth = 0.5)
        self.ch2_nstd, = self.nstdplot.plot(self.nstd_time, self.nstd_data[1], '-r', label ='Channel 2', linewidth = 0.5)
        self.ch3_nstd, = self.nstdplot.plot(self.nstd_time, self.nstd_data[2], '-g', label ='Channel 3', linewidth = 0.5)

        self.nstdplot.legend(loc='upper left')

        self.fig.show()

        return True

    def plot_update(self):
        # Send all new data to plot
        self.ch1.set_ydata(self.data[0])
        self.ch2.set_ydata(self.data[1])
        self.ch3.set_ydata(self.data[2])
        self.ax.relim()
        self.ax.autoscale_view()

        self.ft1.set_ydata(self.ft_data[0])
        self.ftplot.relim()
        self.ftplot.autoscale_view()

        self.ch1_nstd.set_ydata(self.nstd_data[0])
        self.ch2_nstd.set_ydata(self.nstd_data[1])
        self.ch3_nstd.set_ydata(self.nstd_data[2])
        self.nstdplot.relim()
        self.nstdplot.autoscale_view()

        # Checks if there are too many packets left in serial, e.g. if speed of processing is fast enough
        packets_inwaiting = int(np.round(self.arduino.inWaiting()/self.packsize))
        if packets_inwaiting >= 50:
            print('Update rate is slow: {} packets inwaiting, {} second delay.'.format(packets_inwaiting, np.round(packets_inwaiting/256,2)))

def main():
    emg = EMG('COM3')
    arduino = emg.establish_connection()
    if arduino: emg.realtime_emg()

if __name__ == '__main__':
    main()
