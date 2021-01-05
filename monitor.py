import argparse
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.express as px
import pandas as pd


parser = argparse.ArgumentParser(prog='monitor')
parser.add_argument('--input', dest='file', metavar='', help='specify the path and date of the data&log files to be monitored. E.g.: --input data_output/2021-01-05')
args = parser.parse_args()

data_file = f'{args.file}_data.csv'
log_file = f'{args.file}_log.txt'

# file = "data_brood/2020-12-13_data.csv"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.H1(children='Hello hatchling', style={
    'textAlign': 'center'
    }),

    html.Div(children='''
    Live monitoring of the values collected & controlled by hatchling
    ''', style={
    'textAlign': 'center',
    }),

    html.Div(children='''

    ''', style={
    'textAlign': 'center',
    'padding': 10
    }),

    html.Div(children='''
    Log File
    ''', style={
    'textAlign': 'left',
    }),

    html.Div(id='log-div-output', style={'whiteSpace': 'pre-line', 'overflow-y': 'auto', 'height': '100px'}),

    html.Div(children='''
    ''', style={
    'textAlign': 'center',
    'padding': 30
    }),

    html.Div([
        html.Div([
            daq.Gauge(

            color="#0000FF",
            size=300,
            id='gauge-temp',

            label='Temperature',
            units='°C',
            showCurrentValue=True,
            value=0,
            min=0,
            max=60),
    ], className='six columns'),

        html.Div([
            daq.Gauge(
            color="#FF0000",
            size=300,
            id='gauge-humid',
            label='Humidity',
            units='%',
            showCurrentValue=True,
            value=0,
            min=0,
            max=100),
    ], className='six columns'),
    ], className="row"),

    html.H3(children='''
    Live update of last 20 data points
    ''', style={
    'textAlign': 'center',
    }),

    dcc.Graph(id='chart'),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0), #2s

    html.H3(children='''
    Live update of last day
    ''', style={
    'textAlign': 'center',
    }),

    dcc.Graph(id='chart_day'),
    dcc.Interval(id='interval-component_day', interval=600000, n_intervals=0), #10 min

    html.H3(children='''
    Live update of all data points so far
    ''', style={
    'textAlign': 'center',
    }),

    dcc.Graph(id='chart_full'),
    dcc.Interval(id='interval-component_full', interval=3600000, n_intervals=0) # milliseconds # 3600000 1h
])

@app.callback(Output('log-div-output', 'children'),
              [Input('interval-component','n_intervals')])

def log_content(n):
    log = open(log_file)
    line = log.readlines()
    return line


# show only current snapshot of last 5 values
@app.callback(Output('chart', 'figure'),
              Output('gauge-temp', 'value'),
              Output('gauge-humid', 'value'),
              Input('interval-component', 'n_intervals'))

def update_graphs(n):
    headers = ["Time", "Humidity", "Temperature", "humid_raw", "temp_raw", "sensor", "Set Point: Humidity", "Set Point: Temperature", "Duty Cycle"]
    df = pd.read_csv(data_file, names=headers, index_col=0)
    # df.columns = headers
    # print(df)

    df_chart = df[["Temperature", "Humidity", "Set Point: Temperature", "Set Point: Humidity", "Duty Cycle"]]
    df_chart = df_chart.tail(20)

    df_gauge = df[["Temperature"]]
    df_gauge = df.tail(1)
    value = df_gauge.Temperature.item()

    df_gauge_2 = df[["Humidity"]]
    df_gauge_2 = df.tail(1)
    value_2 = df_gauge_2.Humidity.item()
    # print(df)

    fig = px.line(df_chart)
    fig.update_traces(mode='markers+lines')


    return fig, value, value_2


# create chart with daily dataset
@app.callback(Output('chart_day', 'figure'),
              Input('interval-component_day', 'n_intervals'))

def make_chart(n):
    headers = ["Time", "Humidity", "Temperature", "humid_raw", "temp_raw", "sensor", "Set Point: Humidity", "Set Point: Temperature", "Duty Cycle"]
    df = pd.read_csv(data_file, names=headers, index_col=0)
    # df.columns = headers
    # print(df)

    df = df[["Temperature", "Humidity", "Set Point: Temperature", "Set Point: Humidity", "Duty Cycle"]]
    df = df.tail(20000)

    # print(df)

    fig = px.line(df)
    fig.update_traces(mode='markers+lines')
    return fig


# create chart with entire dataset
@app.callback(Output('chart_full', 'figure'),
              Input('interval-component_full', 'n_intervals'))

def make_chart(n):
    headers = ["Time", "Humidity", "Temperature", "humid_raw", "temp_raw", "sensor", "Set Point: Humidity", "Set Point: Temperature", "Duty Cycle"]
    df = pd.read_csv(data_file, names=headers, index_col=0)
    # df.columns = headers
    # print(df)

    df = df[["Temperature", "Humidity", "Set Point: Temperature", "Set Point: Humidity", "Duty Cycle"]]

    # print(df)

    fig = px.line(df)
    fig.update_traces(mode='markers+lines')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port="8050") # 0.0.0.0 to run as localhost
