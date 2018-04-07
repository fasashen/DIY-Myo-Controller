import dash
from dash.dependencies import Output, Event, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import numpy as np
import emg_api


app = dash.Dash(__name__)
app.layout = html.Div([

        html.Div([
            html.H3(children='EMG Dashboard', className='col s12'),

            html.H6(
                children='''Realtime EMG data processing''',
                className='col s4'),

            dcc.Slider(
                id='slider-update',
                min=1,
                max=6,
                marks={i+1: 'Channel {}'.format(i+1) for i in range(6)},
                step=None,
                value=1,
                className='col s4 offset-s2'),


        ],className='row', style={'margin-left':30,'margin-right':30,'vertical-align': 'middle'}),




        html.Div([
            html.Div([
                dcc.Graph(
                    id='voltage-graph',
                    animate=True
                    )
            ], className="col s6"),

            html.Div([
                dcc.Graph(
                    id='freq-graph',
                    animate=True
                    )
            ], className="col s6")

        ], className="row", style={'width':'100%','float':'center'}),

        html.Div([

            dcc.Graph(
                id='nanstd-graph',
                animate=True
                )

        ], className="row", style={'width':'100%','float':'center', 'display': 'inline-block'}),

        dcc.Interval(
            id='graph-update',
            interval=2000),

        dcc.Interval(
            id='nanstd-update',
            interval=2000),

        dcc.Interval(
            id='data-update',
            interval=20),

        html.Div(id='hidden-div', style={'display':'none'})

    ], className="container",style={'float':'center','width':'95%','margin-left':30,'margin-right':30,'max-width':2000}
)




@app.callback(Output('hidden-div', 'style'),
              events=[Event('data-update', 'interval')])
def update_all_data():
    emg.read_packs()

    # Fourie transform
    emg.ft0_data[0] = np.fft.fft(emg.data[0],emg.nfft)
    emg.ft_data[0] = [10*np.log10(abs(x)**2/emg.frequency/emg.plotsize) for x in emg.ft0_data[0][0:int(emg.nfft/2)]]

    # Standard deviation
    emg.compute_nanstd()
    emg.nstd_time.append(emg.nstd_time[-1]+emg.numread*(1/emg.frequency))

    packets_inwaiting = emg.inwaiting()
    if packets_inwaiting >= 50:
        print('Update rate is slow: {} packets inwaiting, {} second delay.'.format(packets_inwaiting, np.round(packets_inwaiting/256,2)))

    return {'display':'none'}


@app.callback(Output('voltage-graph', 'figure'),
              events=[Event('graph-update', 'interval')],
              inputs=[Input('slider-update', 'value')])
def update_voltage_plot(channels_to_plot):

    connection_check()
    volt = emg.data

    channels = range(0,channels_to_plot)
    voltage_plots = []

    for ch in channels:
        voltage_plots.append(go.Scatter(
                x = list(X),
                y = list(volt[ch]),
                name ='Channel {}'.format(ch+1),
                mode = 'lines'
                ))

    return {'data': voltage_plots,'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                yaxis=dict(range=[min(volt[0])-10,max(volt[0])+10]),
                                                title="Raw Voltage Data")}


@app.callback(Output('nanstd-graph', 'figure'),
              events=[Event('nanstd-update', 'interval')],
              inputs=[Input('slider-update', 'value')])
def update_nanstd_plot(channels_to_plot):

    connection_check()
    nanstd = emg.nstd_data
    x_nanstd = emg.nstd_time

    channels = range(0,channels_to_plot)
    nanstd_plots = []

    for ch in channels:
        nanstd_plots.append(go.Scatter(
                x = list(x_nanstd),
                y = list(nanstd[ch]),
                name ='Channel {}'.format(ch+1),
                mode = 'lines'
                ))

    return {'data': nanstd_plots,'layout' : go.Layout(xaxis=dict(range=[min(x_nanstd),max(x_nanstd)]),
                                                yaxis=dict(range=[min(nanstd[0]),max(nanstd[0])]),
                                                title="Standard deviation")}


@app.callback(Output('freq-graph', 'figure'),
              events=[Event('graph-update', 'interval')],
              inputs=[Input('slider-update', 'value')])
def update_freq_plot(channels_to_plot):

    connection_check()
    freq = emg.ft_data
    x_freq = emg.ft_x

    channels = range(0,channels_to_plot)
    nanstd_plots = []

    for ch in channels:
        nanstd_plots.append(go.Scatter(
                x = list(x_freq),
                y = list(freq[ch]),
                name ='Channel {}'.format(ch+1),
                mode = 'lines'
                ))

    return {'data': nanstd_plots,'layout' : go.Layout(xaxis=dict(range=[min(x_freq),max(x_freq)]),
                                                yaxis=dict(range=[min(freq[0]),max(freq[0])]),
                                                title="Fourie transform")}



external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})



def connection_check():
    if 'connection' not in globals():
        global connection
        connection = emg.establish_connection()
    if not connection:
        print('Trying to establish connection with arduino')
        connection = emg.establish_connection()

if __name__ == '__main__':

    emg = emg_api.EMG('COM3',numread=30, plotting=False, plotsize = 256, nstd_timespan = 1280)
    X = emg.x_time
    channels = range(0,1)

    app.run_server(debug=True)
