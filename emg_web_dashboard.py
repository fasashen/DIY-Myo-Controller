import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly
import random
import plotly.graph_objs as go
from collections import deque

zeros = list(np.zeros(256))
print(zeros)

X = [ deque(list(np.zeros(256)),maxlen=256) for x in range(0,6)]
print(X)

Y = deque([1,2,3],maxlen=20)
print(list(Y))

#
#
# app = dash.Dash(__name__)
# app.layout = html.Div(
#     [
#         dcc.Graph(id='live-graph', animate=True),
#         dcc.Interval(
#             id='graph-update',
#             interval=1*1000
#         ),
#     ]
# )
#
# @app.callback(Output('live-graph', 'figure'),
#               events=[Event('graph-update', 'interval')])
# def update_graph_scatter():
#     X.append(X[-1]+1)
#     Y.append(Y[-1]+Y[-1]*random.uniform(-0.1,0.1))
#
#     data = plotly.graph_objs.Scatter(
#             x=list(X),
#             y=list(Y),
#             name='Scatter',
#             mode= 'lines+markers'
#             )
#
#     return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
#                                                 yaxis=dict(range=[min(Y),max(Y)]),)}
#


# if __name__ == '__main__':
#     print(X)
    # app.run_server(debug=True)
