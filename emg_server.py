import os
import emg_api
import time
import atexit
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask
from flask import request
import json
from time import gmtime, strftime
import emg_web_dashboard as ewd

app = Flask(__name__, static_url_path='/static')

@app.route("/")
def index():
    return app.send_static_file('dash.html')

@app.route("/emg/", methods=['GET'])
@app.route("/emg/<channels_to_plot>", methods=['GET'])
def get_emg(channels_to_plot=1):

    channels_to_plot = int(channels_to_plot)

    channels = range(0,channels_to_plot)
    voltage = []
    nanstd = []

    for channel in channels:
        voltage.append(list(emg.data[channel]))
        nanstd.append(list(emg.nstd_data[channel]))

    data = json.dumps(
        {'voltage_y': list(voltage),
         'voltage_x': list(emg.x_time),
         'nanstd_y': list(nanstd),
         'nanstd_x': list(emg.nstd_time),
         'freq_y': list(emg.ft_data),
         'freq_x': list(emg.ft_x),
         'server_time': strftime("%H:%M:%S", gmtime())},
        sort_keys=False,
        indent=4,
        separators=(',', ': '))

    return data

# Updates EMG data in realtime
def emg_realtime_update():
    emg.read_packs()
    packets_inwaiting = emg.inwaiting()
    if packets_inwaiting >= 50:
        print('Update rate is slow: {} packets inwaiting, {} second delay.'.format(packets_inwaiting, np.round(packets_inwaiting/256,2)))


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=emg_realtime_update,
    trigger=IntervalTrigger(seconds=0.020),
    replace_existing=True)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    try:
        emg = emg_api.EMG('COM3',numread=20, plotting=False, plotsize = 256, nstd_timespan = 2560)
        connection = emg.establish_connection()
    except Exception as e:
        print('Connection to arduino failed: {}'.format(e))
    print('Flask server started')
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, threaded=True)
