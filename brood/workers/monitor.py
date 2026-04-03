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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json


parser = argparse.ArgumentParser(prog='monitor')
parser.add_argument('--input', dest='folder', metavar='', help='specify the data folder path. E.g.: --input data/2025-12-18_PCNA_test_run_v0')
args = parser.parse_args()

# Construct file paths - files are in the data folder
data_file = os.path.join(args.folder, 'data.csv')
log_file = os.path.join(args.folder, 'hatch.log')

# Track if degraded mode email has been sent to avoid spam
degraded_mode_email_sent = False

# Track if startup email has been sent to avoid spam
startup_email_sent = False

# Global cache for CSV data to avoid redundant reads
class DataCache:
    """Cache for CSV data with timestamp tracking to minimize file reads"""
    def __init__(self):
        self.df = None
        self.last_mtime = None
        self.last_read_time = 0
        self.cache_ttl = 0.5  # Cache for 500ms before re-reading
    
    def get_data(self):
        """Get cached dataframe, re-reading file only if it's been modified"""
        import time
        try:
            current_time = time.time()
            
            # Check if cache is still valid (TTL not expired)
            if self.df is not None and (current_time - self.last_read_time) < self.cache_ttl:
                return self.df
            
            # Check if file exists and has been modified
            if not os.path.exists(data_file):
                return None
            
            current_mtime = os.path.getmtime(data_file)
            
            # Re-read only if file was modified or cache is expired
            if self.last_mtime is None or current_mtime != self.last_mtime or (current_time - self.last_read_time) >= self.cache_ttl:
                self.df = pd.read_csv(data_file, index_col=0)
                self.last_mtime = current_mtime
                self.last_read_time = current_time
            
            return self.df
        except Exception as e:
            print(f"❌ Error reading data cache: {str(e)}")
            return None

data_cache = DataCache()

# Load email configuration from external JSON file
def load_email_config():
    """Load email configuration from email_config.json (not tracked by git)"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'email_config.json')
    
    # Default config if file doesn't exist
    default_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'your-email@gmail.com',
        'sender_password': 'your-app-password',
        'recipient_email': 'your-email@gmail.com',
        'enabled': False
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            print(f"⚠️  Warning: email_config.json not found at {config_path}")
            print("   Email notifications are disabled. To enable:")
            print(f"   1. Create {config_path}")
            print("   2. Add your email credentials (see example in README)")
            return default_config
    except Exception as e:
        print(f"❌ Failed to load email config: {str(e)}")
        return default_config

EMAIL_CONFIG = load_email_config()

def send_degraded_mode_email():
    """Send email alert when degraded mode is detected"""
    if not EMAIL_CONFIG['enabled']:
        return False
    
    try:
        # Create email message
        subject = f"🚨 Hatchling Alert: Degraded Mode Detected - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
Hatchling Incubator Alert!

⚠️  DEGRADED MODE DETECTED ⚠️

The incubator has detected degraded mode operation - only one temperature/humidity sensor is available.

Details:
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Data Folder: {args.folder}
- Status: One of the two sensors has failed

Action Required:
1. Check the physical connections of both HTU31D sensors
2. Verify I2C addresses (0x40 and 0x41)
3. Review the log file for error details
4. Restart the incubator once the sensor issue is fixed: python hatchling.py --run

The incubator will shut down after this alert to prevent operating in degraded mode.

Log file location: {log_file}

---
Hatchling Incubator Controller
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {EMAIL_CONFIG['recipient_email']}")
        return True
    
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def send_startup_email():
    """Send email alert when Hatchling starts up"""
    if not EMAIL_CONFIG['enabled']:
        return False
    
    try:
        # Read the log file to get startup details
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Extract species from init.txt if available
        init_file = os.path.join(args.folder, '..', 'init.txt')
        species = "Unknown"
        if os.path.exists(init_file):
            try:
                with open(init_file, 'r') as f:
                    init_content = f.read().strip()
                    # Format: YYYY-MM-DD HH:MM:SS|species
                    if '|' in init_content:
                        species = init_content.split('|')[1]
            except Exception:
                pass
        
        # Create email message
        subject = f"✅ Hatchling Started - {species} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
Hatchling Incubator Started!

✅ STARTUP NOTIFICATION

The Hatchling incubator has been started and is now running.

Details:
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Data Folder: {args.folder}
- Species: {species}
- Status: Initializing incubation cycle

System Status:
- Two temperature/humidity sensors configured
- PID controller initialized
- Heater and fan ready

Monitor Dashboard:
- Access the live monitoring dashboard at: http://localhost:8050

Log file location: {log_file}

---
Hatchling Incubator Controller
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        print(f"✅ Startup email sent successfully to {EMAIL_CONFIG['recipient_email']}")
        return True
    
    except Exception as e:
        print(f"❌ Failed to send startup email: {str(e)}")
        return False

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
    html.H1(children='Hatchling 2.0', style={'textAlign': 'center'}),

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
                # Individual sensor readings below the gauge
                html.Div([
                    html.Div(id='sensor-temp-0-box', style={
                        'padding': '6px',
                        'margin': '4px 2px',
                        'border': '1px solid #444',
                        'backgroundColor': '#0a0f18',
                        'color': '#aef6ff',
                        'textAlign': 'center',
                        'fontSize': '12px',
                        'borderRadius': '4px'
                    }, className='six columns'),
                    html.Div(id='sensor-temp-1-box', style={
                        'padding': '6px',
                        'margin': '4px 2px',
                        'border': '1px solid #444',
                        'backgroundColor': '#0a0f18',
                        'color': '#aef6ff',
                        'textAlign': 'center',
                        'fontSize': '12px',
                        'borderRadius': '4px'
                    }, className='six columns'),
                ], className='row', style={'marginTop': '8px'}),
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

    # html.H3('All data points (1 hour updates)', style={'textAlign': 'center'}),
    # dcc.Graph(id='chart_full'),
    # dcc.Interval(id='interval-component_full', interval=3600000, n_intervals=0)  # 1h
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
    global degraded_mode_email_sent, startup_email_sent
    
    # Read entire log file, reverse the lines, and return with latest on top
    try:
        with open(log_file, 'r') as log:
            lines = log.readlines()
            if not lines:
                return 'Log file is empty or not yet created'
            
            content = ''.join(lines)  # Full content for checking alerts
            
            # Check for degraded mode warning
            if 'Operating in degraded mode' in content and not degraded_mode_email_sent:
                degraded_mode_email_sent = True
                print("📧 Degraded mode detected! Sending email notification...")
                send_degraded_mode_email()
            
            # Check for startup messages - look for key startup indicators
            startup_indicators = [
                'Initializing PID controller',
                'Found HTU31D Sensor 0',
                'PID Parameters -'
            ]
            
            has_startup_indicators = any(indicator in content for indicator in startup_indicators)
            
            # Only send email if:
            # 1. We haven't sent it yet
            # 2. We find startup indicators
            # 3. The log file was recently created/updated (within last 60 seconds)
            if has_startup_indicators and not startup_email_sent:
                import time
                log_mtime = os.path.getmtime(log_file)
                current_time = time.time()
                time_diff = current_time - log_mtime
                
                # If log file was modified within last 60 seconds, it's a fresh startup
                if time_diff < 60:
                    startup_email_sent = True
                    print("📧 Fresh startup detected! Sending startup notification email...")
                    send_startup_email()
            
            # Reverse the order so latest is at the top
            log_display = ''.join(reversed(lines))
            return log_display if log_display.strip() else 'No log entries found'
    
    except FileNotFoundError:
        return f'Log file not found: {log_file}'
    except Exception as e:
        return f'Error reading log file: {str(e)}'


# Update temperature gauge with the latest Flow Cell Temperature
@app.callback(Output('gauge-temp', 'value'), Input('interval-component', 'n_intervals'))
def update_temp_gauge(n):
    try:
        df = data_cache.get_data()
        if df is None or df.empty:
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
    try:
        df = data_cache.get_data()
        if df is None or df.empty:
            return 0
        last_series = df["Humidity"].dropna()
        if last_series.empty:
            return 0
        value = float(last_series.tail(1).item())
        return value
    except Exception:
        return 0


# Update display box with Temp_0 sensor reading
@app.callback(Output('sensor-temp-0-box', 'children'), Input('interval-component', 'n_intervals'))
def update_sensor_temp_0_box(n):
    try:
        df = data_cache.get_data()
        if df is None or df.empty or "Temp_0" not in df.columns:
            return 'Sensor 0: N/A'
        last_series = df["Temp_0"].dropna()
        if last_series.empty:
            return 'Sensor 0: N/A'
        value = float(last_series.tail(1).item())
        return f'Sensor 0: {value:.2f} °C'
    except Exception:
        return 'Sensor 0: N/A'


# Update display box with Temp_1 sensor reading
@app.callback(Output('sensor-temp-1-box', 'children'), Input('interval-component', 'n_intervals'))
def update_sensor_temp_1_box(n):
    try:
        df = data_cache.get_data()
        if df is None or df.empty or "Temp_1" not in df.columns:
            return 'Sensor 1: N/A'
        last_series = df["Temp_1"].dropna()
        if last_series.empty:
            return 'Sensor 1: N/A'
        value = float(last_series.tail(1).item())
        return f'Sensor 1: {value:.2f} °C'
    except Exception:
        return 'Sensor 1: N/A'


# Update display box with the latest Set Point: Temperature
@app.callback(Output('set-temp-box', 'children'), Input('interval-component', 'n_intervals'))
def update_set_temp_box(n):
    try:
        df = data_cache.get_data()
        if df is None or df.empty or "Set_Temp" not in df.columns:
            return 'Set temperature: N/A'
        last_series = df["Set_Temp"].dropna()
        if last_series.empty:
            return 'Set temperature: N/A'
        value = float(last_series.tail(1).item())
        return f'Set temperature: {value:.2f} °C'
    except Exception:
        return 'Set temperature: N/A'


# Update display box with the latest Set Humidity
@app.callback(Output('env-temp-box', 'children'), Input('interval-component', 'n_intervals'))
def update_env_temp_box(n):
    try:
        df = data_cache.get_data()
        if df is None or df.empty or "Set_Humid" not in df.columns:
            return 'Set humidity: N/A'
        last_series = df["Set_Humid"].dropna()
        if last_series.empty:
            return 'Set humidity: N/A'
        value = float(last_series.tail(1).item())
        return f'Set humidity: {value:.2f} %'
    except Exception:
        return 'Set humidity: N/A'



# create chart with daily dataset
@app.callback(Output('chart_day', 'figure'), Input('interval-component_day', 'n_intervals'))
def make_chart_day(n):
    try:
        df = data_cache.get_data()
        if df is None:
            fig = px.line()
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
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
# @app.callback(Output('chart_full', 'figure'), Input('interval-component_full', 'n_intervals'))
# def make_chart_full(n):
#     try:
#         df = pd.read_csv(data_file, index_col=0)
#     except Exception:
#         fig = px.line()
#         fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
#         return fig
# 
#     if df.empty or "Temperature" not in df.columns:
#         fig = px.line()
#         fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
#         return fig
# 
#     df = df[["Temperature", "Set_Temp", "Duty_Cycle", "Humidity"]]
#     
#     # Convert all columns to numeric to ensure proper y-axis scaling
#     df = df.apply(pd.to_numeric, errors='coerce')
# 
#     # Build figure with dual y-axes using graph_objects
#     fig = go.Figure()
#     
#     # Add temperature traces to primary y-axis
#     fig.add_trace(go.Scatter(x=df.index, y=df["Temperature"], 
#                              name="Temperature", mode='markers+lines', yaxis='y1'))
#     fig.add_trace(go.Scatter(x=df.index, y=df["Set_Temp"], 
#                              name="Set_Temp", mode='markers+lines', yaxis='y1'))
#     fig.add_trace(go.Scatter(x=df.index, y=df["Humidity"], 
#                              name="Humidity", mode='markers+lines', yaxis='y1'))
#     
#     # Add duty cycle to secondary y-axis (hidden by default)
#     fig.add_trace(go.Scatter(x=df.index, y=df["Duty_Cycle"], 
#                              name="Duty_Cycle", mode='markers+lines', yaxis='y2', visible='legendonly'))
#     
#     fig.update_layout(
#         template='plotly_dark',
#         paper_bgcolor='rgba(0,0,0,0)',
#         plot_bgcolor='rgba(0,0,0,0)',
#         xaxis_title='Time',
#         yaxis=dict(title='Temperature (°C) / Humidity (%)', side='left'),
#         yaxis2=dict(title='Duty Cycle (%)', side='right', overlaying='y', range=[0, 100])
#     )
#     return fig


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="8050")  # 0.0.0.0 to run as localhost