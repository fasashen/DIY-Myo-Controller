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
from io import StringIO
import json
from time import gmtime, strftime
import requests


app = dash.Dash(__name__)

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})

app.layout = html.Div([

        html.Div([
            html.H3(children='EMG Dashboard', className='col s12'),

            html.H6(
                children='''Realtime EMG data processing''',
                className='col s4'),

            dcc.Slider(
                id='slider-update',
                updatemode='drag',
                min=1,
                max=6,
                marks={i+1: 'Channel {}'.format(i+1) for i in range(6)},
                step=None,
                value=2,
                className='col s4 offset-s2'),

        ], className='row', style={'margin-left':30,'margin-right':30,'vertical-align': 'middle'}),

        html.Div(
            id='time-div',
            className="row",
            style={'margin-left':30,'margin-right':30,'vertical-align': 'middle'}),

        html.Div([

            dcc.Graph(
                id='nanstd-graph',
                animate=True
                )

            ], className="row", style={'width':'100%','float':'center', 'display': 'inline-block'}),

            dcc.Interval(
                id='graph-update',
                interval=1*1000),

            dcc.Interval(
                id='nanstd-update',
                interval=1*1000),

            dcc.Interval(
                id='data-update',
                interval=1*2000),

            html.Div(id='hidden-div', style={'display':'none'}),

            html.Div([
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
                ], className='row', style={'margin-left':30,'margin-right':30,'vertical-align': 'middle'}),

        ],
        className="container",
        style={'float':'center','width':'95%','margin-left':30,'margin-right':30,'max-width':2000}

)


@app.callback(Output('time-div', 'children'),
              events=[Event('data-update', 'interval')],
              inputs=[Input('slider-update', 'value')])
def update_all_data(channels_to_plot):

    global data

    r = requests.get('http://localhost:5000/emg/{}'.format(channels_to_plot))
    data = r.json()
    print(r,data['server_time'])



    server_time = html.H6(
        children='Server time: ' + data['server_time'],
        className="col s12",
        style={'width':'100%','float':'center','text-align': 'center'})


    return [server_time]



@app.callback(Output('voltage-graph', 'figure'),
              events=[Event('graph-update', 'interval')])
def update_voltage_plot():

    global data

    volt = data['voltage_y']
    X = data['voltage_x']
    channels_to_plot = len(volt)

    channels = range(0,channels_to_plot)
    maxval, minval = max_min(volt[:channels_to_plot])
    voltage_plots = []

    for ch in channels:
        voltage_plots.append(go.Scatter(
                x = list(X),
                y = list(volt[ch]),
                name ='Channel {}'.format(ch+1),
                mode = 'lines'
                ))

    return {'data': voltage_plots,'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                yaxis=dict(range=[minval,maxval]),
                                                title="Raw Voltage Data")}


@app.callback(Output('nanstd-graph', 'figure'),
              events=[Event('nanstd-update', 'interval')])
def update_nanstd_plot():

    global data

    nanstd = data['nanstd_y']
    x_nanstd = data['nanstd_x']
    channels_to_plot = len(nanstd)

    channels = range(0,channels_to_plot)
    maxval, minval = max_min(nanstd[:channels_to_plot])
    nanstd_plots = []

    for ch in channels:
        nanstd_plots.append(go.Scatter(
                x = list(x_nanstd),
                y = list(nanstd[ch]),
                name ='Channel {}'.format(ch+1),
                mode = 'lines'
                ))

    return {'data': nanstd_plots,'layout' : go.Layout(xaxis=dict(range=[min(x_nanstd),max(x_nanstd)]),
                                                yaxis=dict(range=[minval,maxval]),
                                                title="Standard deviation, Plot Time: {}".format(strftime("%H:%M:%S", gmtime())))}

@app.callback(Output('freq-graph', 'figure'),
              events=[Event('graph-update', 'interval')])
def update_freq_plot():

    global data

    freq = data['freq_y']
    x_freq = data['freq_x']
    channels_to_plot = len(freq)

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



def max_min(lists):
    maxval = max(lists[0])
    minval = min(lists[0])
    for list in lists:
        if maxval < max(list): maxval = max(list)
        if minval > min(list): minval = min(list)
    return maxval, minval

if __name__ == '__main__':
    data = {}
    app.run_server(debug=True)
