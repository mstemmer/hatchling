import argparse
import os
import re
import dash
from dash.dependencies import Input, Output
from dash import dcc
from dash import html
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


parser = argparse.ArgumentParser(prog='monitor')
parser.add_argument('--input', dest='folder', metavar='', help='specify the data folder path. E.g.: --input data/2025-12-18_PCNA_test_run_v0')
args = parser.parse_args()

# Construct file paths - files are in the data folder
data_file = os.path.join(args.folder, 'data.csv')
log_file = os.path.join(args.folder, 'hatch.log')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Load custom CSS for dark mode styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Dark mode overrides for the Dash app */
            html, body {
              background-color: #0f1113;
              color: #e6eef6;
            }

            /* Header styles */
            h1, h3 {
              color: #e6eef6;
            }

            /* Log box styling */
            #log-div-output {
              background-color: #121416 !important;
              color: #e6eef6 !important;
              border: 1px solid #2b2f33 !important;
            }

            /* Make the gauge background transparent so it sits well on dark bg */
            .daq-gauge {
              background: transparent !important;
            }

            /* Make chart container transparent */
            .js-plotly-plot {
              background: transparent !important;
            }

            /* Adjust link and text colors inside the app */
            a, p, div, span {
              color: #e6eef6;
            }

            /* Adjust small UI elements */
            .row, .six.columns {
              padding: 6px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


app.layout = html.Div(children=[
    html.H1(children='TPU monitor', style={'textAlign': 'center'}),

    html.Div(children='''
    Live monitoring of the values collected & controlled by Hatchling
    ''', style={'textAlign': 'center'}),

    # Current program name
    html.Div(id='program-name-box', style={
        'textAlign': 'center',
        'padding': '10px',
        'margin': '10px auto',
        'maxWidth': '600px',
        'border': '1px solid #333',
        'backgroundColor': '#0b1220',
        'color': '#eef6ff',
        'fontWeight': 'bold',
        'fontSize': '18px'
    }),

    html.Div(children='', style={'textAlign': 'center', 'padding': 10}),

    # Row with Log File (left) and Temperature Gauge (right)
    html.Div([
        html.Div([
            # 1. Current step box
            html.Div(id='current-step-box', style={
                'marginBottom': '8px',
                'padding': '10px',
                'border': '1px solid #333',
                'backgroundColor': '#0b1220',
                'color': '#eef6ff',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'fontSize': '16px'
            }),
            # 2. Set temperature and environment temperature boxes
            html.Div([
                html.Div(id='set-temp-box', style={
                    'padding': '8px',
                    'border': '1px solid #333',
                    'backgroundColor': '#0b1220',
                    'color': '#eef6ff',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'marginRight': '4px'
                }, className='six columns'),
                html.Div(id='env-temp-box', style={
                    'padding': '8px',
                    'border': '1px solid #333',
                    'backgroundColor': '#0b1220',
                    'color': '#eef6ff',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'marginLeft': '4px'
                }, className='six columns'),
            ], className='row', style={'marginBottom': '8px'}),
            # 3. Log File window
            html.Div('Log File', style={'textAlign': 'left'}),
            html.Div(id='log-div-output', style={
                'whiteSpace': 'pre-line',
                'overflowY': 'auto',
                'height': '180px',
                'padding': '10px',
                'border': '1px solid #333',
                'backgroundColor': '#0f1720',
                'color': '#eef6ff'
            }),
        ], className='four columns'),

        html.Div([
            # Temperature and Humidity Gauges side by side
            # Temperature Gauge
            html.Div([
                html.Div('Temperature', style={
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'fontWeight': '700',
                    'color': '#eef6ff',
                    'marginBottom': '4px'
                }),
                daq.Gauge(
                    color="#22FF00",
                    size=300,
                    id='gauge-temp',
                    label='',
                    units='°C',
                    showCurrentValue=True,
                    value=0,
                    min=0,
                    max=80
                ),
            ], className='six columns'),
            
            # Humidity Gauge
            html.Div([
                html.Div('Humidity', style={
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'fontWeight': '700',
                    'color': '#eef6ff',
                    'marginBottom': '4px'
                }),
                daq.Gauge(
                    color="#00BFFF",
                    size=300,
                    id='gauge-humidity',
                    label='',
                    units='%',
                    showCurrentValue=True,
                    value=0,
                    min=0,
                    max=100
                ),
            ], className='six columns'),
        ], className='eight columns'),
    ], className='row'),

    # Interval used to refresh the log output and gauge
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),  # 2s

    html.H3('Last three hours (10 min updates)', style={'textAlign': 'center'}),
    dcc.Graph(id='chart_day'),
    dcc.Interval(id='interval-component_day', interval=600000, n_intervals=0),  # 10 min

    html.H3('All data points (1 hour updates)', style={'textAlign': 'center'}),
    dcc.Graph(id='chart_full'),
    dcc.Interval(id='interval-component_full', interval=3600000, n_intervals=0)  # 1h
])


# Update current step box with latest phase from log entry
@app.callback(Output('current-step-box', 'children'), Input('interval-component', 'n_intervals'))
def update_current_step(n):
    import re
    
    try:
        if not os.path.exists(log_file):
            return 'Log file not found'
            
        with open(log_file, 'r') as log:
            lines = log.readlines()
        
        if not lines:
            return 'No log entries yet'
        
        # Search for the most recent line containing capital "PHASE"
        for line in reversed(lines):
            # Match lines containing "PHASE" (capital letters)
            if 'PHASE' in line:
                # Extract the whole line and clean it up
                phase_line = line.strip()
                # Remove timestamp if present (format: YYYY-MM-DD HH:MM:SS)
                phase_info = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ', '', phase_line)
                # Remove log level prefix (INFO:, WARNING:, etc.)
                phase_info = re.sub(r'^[A-Z]+:\s*', '', phase_info)
                return f'Current phase: {phase_info}'
        
        return 'No active phase'
    
    except FileNotFoundError:
        return 'Log file not found'
    except Exception as e:
        return f'Phase: Error - {str(e)}'


@app.callback(Output('program-name-box', 'children'), Input('interval-component', 'n_intervals'))
def update_program_name(n):
    try:
        # Search for "Load incubation program:" line in the log file
        if not os.path.exists(log_file):
            return 'No program loaded'
        
        with open(log_file, 'r') as log:
            lines = log.readlines()
        
        # Search for the most recent "Load incubation program:" line
        for line in reversed(lines):
            if 'Load incubation program:' in line:
                # Extract the program name after the colon
                program_info = line.split('Load incubation program:')[-1].strip()
                # Remove log level prefix if present
                program_info = re.sub(r'^[A-Z]+:\s*', '', program_info)
                return f'Current Program: {program_info}'
        
        return 'No program loaded'
    
    except FileNotFoundError:
        return 'No program loaded'
    except Exception as e:
        return f'Program: Unknown ({str(e)})'


@app.callback(Output('log-div-output', 'children'), Input('interval-component', 'n_intervals'))
def log_content(n):
    # Read entire log file, reverse the lines, and return with latest on top
    try:
        with open(log_file, 'r') as log:
            lines = log.readlines()
            if not lines:
                return 'Log file is empty or not yet created'
            # Reverse the order so latest is at the top
            content = ''.join(reversed(lines))
            return content if content.strip() else 'No log entries found'
    except FileNotFoundError:
        return f'Log file not found: {log_file}'
    except Exception as e:
        return f'Error reading log file: {str(e)}'


# Update temperature gauge with the latest Flow Cell Temperature
@app.callback(Output('gauge-temp', 'value'), Input('interval-component', 'n_intervals'))
def update_temp_gauge(n):
    headers = [
        "Time",
        "Temperature",
        "Humidity",
        "Temp_0",
        "Temp_1",
        "Humid_0",
        "Humid_1",
        "Set_Temp",
        "Set_Humid",
        "Duty_Cycle",
    ]
    try:
        df = pd.read_csv(data_file, names=headers, index_col=0)
        if df.empty:
            return 0
        last_series = df["Temperature"].dropna()
        if last_series.empty:
            return 0
        value = float(last_series.tail(1).item())
        return value
    except Exception:
        return 0


# Update humidity gauge with the latest Humidity
@app.callback(Output('gauge-humidity', 'value'), Input('interval-component', 'n_intervals'))
def update_humidity_gauge(n):
    headers = [
        "Time",
        "Temperature",
        "Humidity",
        "Temp_0",
        "Temp_1",
        "Humid_0",
        "Humid_1",
        "Set_Temp",
        "Set_Humid",
        "Duty_Cycle",
    ]
    try:
        df = pd.read_csv(data_file, names=headers, index_col=0)
        if df.empty:
            return 0
        last_series = df["Humidity"].dropna()
        if last_series.empty:
            return 0
        value = float(last_series.tail(1).item())
        return value
    except Exception:
        return 0


# Update display box with the latest Set Point: Temperature
@app.callback(Output('set-temp-box', 'children'), Input('interval-component', 'n_intervals'))
def update_set_temp_box(n):
    headers = [
        "Time",
        "Temperature",
        "Humidity",
        "Temp_0",
        "Temp_1",
        "Humid_0",
        "Humid_1",
        "Set_Temp",
        "Set_Humid",
        "Duty_Cycle",
    ]
    try:
        df = pd.read_csv(data_file, names=headers, index_col=0)
        if df.empty or "Set_Temp" not in df.columns:
            return 'Set temperature: N/A'
        last_series = df["Set_Temp"].dropna()
        if last_series.empty:
            return 'Set temperature: N/A'
        value = float(last_series.tail(1).item())
        return f'Set temperature: {value:.2f} °C'
    except FileNotFoundError:
        return f'Set temperature: data file not found'
    except Exception:
        return 'Set temperature: N/A'


# Update display box with the latest Set Humidity
@app.callback(Output('env-temp-box', 'children'), Input('interval-component', 'n_intervals'))
def update_env_temp_box(n):
    headers = [
        "Time",
        "Temperature",
        "Humidity",
        "Temp_0",
        "Temp_1",
        "Humid_0",
        "Humid_1",
        "Set_Temp",
        "Set_Humid",
        "Duty_Cycle",
    ]
    try:
        df = pd.read_csv(data_file, names=headers, index_col=0)
        if df.empty or "Set_Humid" not in df.columns:
            return 'Set humidity: N/A'
        last_series = df["Set_Humid"].dropna()
        if last_series.empty:
            return 'Set humidity: N/A'
        value = float(last_series.tail(1).item())
        return f'Set humidity: {value:.2f} %'
    except FileNotFoundError:
        return f'Set humidity: data file not found'
    except Exception:
        return 'Set humidity: N/A'



# create chart with daily dataset
@app.callback(Output('chart_day', 'figure'), Input('interval-component_day', 'n_intervals'))
def make_chart_day(n):
    try:
        df = pd.read_csv(data_file, index_col=0)
    except Exception:
        fig = px.line()
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    if df.empty or "Temperature" not in df.columns:
        fig = px.line()
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    df = df[["Temperature", "Set_Temp", "Duty_Cycle", "Humidity"]]
    df = df.tail(10800)
    
    # Convert all columns to numeric to ensure proper y-axis scaling
    df = df.apply(pd.to_numeric, errors='coerce')

    # Build figure with dual y-axes using graph_objects
    fig = go.Figure()
    
    # Add temperature traces to primary y-axis
    fig.add_trace(go.Scatter(x=df.index, y=df["Temperature"], 
                             name="Temperature", mode='markers+lines', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Set_Temp"], 
                             name="Set_Temp", mode='markers+lines', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Humidity"], 
                             name="Humidity", mode='markers+lines', yaxis='y1'))
    
    # Add duty cycle to secondary y-axis (hidden by default)
    fig.add_trace(go.Scatter(x=df.index, y=df["Duty_Cycle"], 
                             name="Duty_Cycle", mode='markers+lines', yaxis='y2', visible='legendonly'))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title='Time',
        yaxis=dict(title='Temperature (°C) / Humidity (%)', side='left'),
        yaxis2=dict(title='Duty Cycle (%)', side='right', overlaying='y', range=[0, 100])
    )
    return fig


# create chart with entire dataset
@app.callback(Output('chart_full', 'figure'), Input('interval-component_full', 'n_intervals'))
def make_chart_full(n):
    try:
        df = pd.read_csv(data_file, index_col=0)
    except Exception:
        fig = px.line()
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    if df.empty or "Temperature" not in df.columns:
        fig = px.line()
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    df = df[["Temperature", "Set_Temp", "Duty_Cycle", "Humidity"]]
    
    # Convert all columns to numeric to ensure proper y-axis scaling
    df = df.apply(pd.to_numeric, errors='coerce')

    # Build figure with dual y-axes using graph_objects
    fig = go.Figure()
    
    # Add temperature traces to primary y-axis
    fig.add_trace(go.Scatter(x=df.index, y=df["Temperature"], 
                             name="Temperature", mode='markers+lines', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Set_Temp"], 
                             name="Set_Temp", mode='markers+lines', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Humidity"], 
                             name="Humidity", mode='markers+lines', yaxis='y1'))
    
    # Add duty cycle to secondary y-axis (hidden by default)
    fig.add_trace(go.Scatter(x=df.index, y=df["Duty_Cycle"], 
                             name="Duty_Cycle", mode='markers+lines', yaxis='y2', visible='legendonly'))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title='Time',
        yaxis=dict(title='Temperature (°C) / Humidity (%)', side='left'),
        yaxis2=dict(title='Duty Cycle (%)', side='right', overlaying='y', range=[0, 100])
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="8050")  # 0.0.0.0 to run as localhost