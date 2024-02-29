import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import power_helper as ph
import numpy as np
import gpxpy

pd.set_option('display.max_columns',50)
pd.set_option('mode.chained_assignment', None)

def load_data(file):
    df = pd.read_csv(file).iloc[:,1:]
    # Riders strikes
    df = df.drop(axis=0, index=248) # 1996 stage 9
    df = df.drop(axis=0, index=234) # 1995 stage 16

    return df

def get_year_data(df):
    # Calculate power for full tour with fixed grade
    total_climbed = df.groupby("year").stage_vertical_meters.sum()
    total_distance = df.groupby("year").stage_distance.sum()
    gc_weights = df.groupby("year").gc_weight.mean()
    gc_time = df.groupby("year").gc_stage_time.sum()
    total_grades = total_climbed/(total_distance*1000)
    velocity = (total_distance*1000)/gc_time
    year_power = ph.cycling_power(total_grades, gc_weights, velocity)
    return year_power

def get_random_scaled_segments(goal, segments, flat_finish = False, arrival_elev=0, min=1, max=25, distance = False):
    # Get random segments totalling goal
    numbers = [np.random.randint(min, max) for _ in range(segments)]
    
    # Scale the numbers proportionally to reach the target sum goal.
    scale_factor = goal / np.sum(numbers)
    scaled_segment = [num * scale_factor for num in numbers]
        
    # Adjust the last number to ensure the sum exactly equals y
    if distance:
        scaled_segment[0] = 0
        scaled_segment[-1] = goal - (np.sum(scaled_segment[:-1]))
    else:
        if flat_finish:
            scaled_segment[-1] = 0
            scaled_segment[-2] = goal - (np.sum(scaled_segment) - scaled_segment[-2])
        else:
            scaled_segment[-1] = -5*scale_factor
            scaled_segment[-2] = goal - (np.sum(scaled_segment) - scaled_segment[-2])
    return scaled_segment

def profile_xy(stage_distance, stage_vertical_meters, peaks=4, flat_finish=False, departure_elev=0, arrival_elev=0):    
    # Convert stage to profile x and y data for graph
    scaled_segment_gain = get_random_scaled_segments(stage_vertical_meters, peaks, flat_finish, arrival_elev, max=10)
    
    scaled_segment_distance = np.cumsum(get_random_scaled_segments(stage_distance, peaks*2, min=15, distance=True))
    
    x = scaled_segment_distance
    y = []
    for i in range(peaks*2):
        y.append(i%2 * (scaled_segment_gain[int(i/2)] + departure_elev) + ((1-i%2) * departure_elev))
    
    y[0] = departure_elev
    y[-1] = arrival_elev
    if flat_finish:
        y[-2] = arrival_elev
    
    return x, y

def stage_to_profile(display_df, index):
    if display_df.iloc[index].year > 2021:
        df_route = get_gpx_route(display_df.iloc[index].year, index+1)
        fig = px.area(df_route, x='total_distance', y='elev', line_shape='linear', color_discrete_sequence=['ForestGreen', 'Aquamarine'])
        fig.update_layout(plot_bgcolor='white', yaxis_title=None, xaxis_title=None, transition_duration=500, transition_easing='cubic-in-out')

        fig.update_xaxes(range = [0,display_df.stage_distance.max()], showgrid=False)
        fig.update_yaxes(range = [ 0,2850 ], showgrid=False)
        return fig
    
    peaks, flat = {'flat':(40, True), 
                     'Hills, flat finish': (20, True), 
                     'Hills, uphill finish': (20, False), 
                     'Mountains, flat finish': (7, True), 
                     'Mountains, uphill finish':(7, False)}.get(display_df.iloc[index].profile_icon)

    x, y = profile_xy(display_df.iloc[index].stage_distance, display_df.iloc[index].stage_vertical_meters, peaks, flat, 500, 1500)
    fig = px.area(x=x, y=np.add(y,50), line_shape='linear', color_discrete_sequence=['ForestGreen', 'Aquamarine'])
    fig.update_layout(plot_bgcolor='white', yaxis_title=None, xaxis_title=None, transition_duration=500, transition_easing='cubic-in-out')

    fig.update_xaxes(range = [0,display_df.stage_distance.max()], showgrid=False)
    fig.update_yaxes(range = [ 0,2850 ], showgrid=False)
    return fig

def get_display_df(df, year):
    display_df = df[['year', 'stage_departure', 'stage_arrival', 
                     'stage_type', 'gc_leader', 'profile_icon', 
                     'stage_distance', 'stage_vertical_meters', 
                     'gc_speed', 'power', 
                     'stage_departure_lat', 'stage_departure_lon',
                     'stage_arrival_lat', 'stage_arrival_lon',]]
    # Replace values for display
    display_df = display_df[display_df.year == int(year)]
    display_df.profile_icon = display_df.profile_icon.replace({'p1':'flat', 'p2':'Hills, flat finish', 'p3': 'Hills, uphill finish',
                         'p4':'Mountains, flat finish', 'p5':'Mountains, uphill finish'})
    display_df.stage_type = display_df.stage_type.replace({'RR':'Race', 'ITT':'TT'})
    display_df.gc_speed = display_df.gc_speed * 3.6
    display_df['stage'] = display_df.stage_departure + '-' + display_df.stage_arrival
    display_df = display_df.round(1)
    # Rename the columns
    return display_df


def get_gpx_route(year, stage_index):
    gpx_file = open('./Routes/{0}/stage-{1}-parcours.gpx'.format(year,stage_index), 'r')

    gpx = gpxpy.parse(gpx_file)
    gpx_dict = dict(lat = [], lon = [], elev = [], dist=[])
    for track in gpx.tracks:
        for segment in track.segments:
            for point_idx in range(1, len(segment.points)):
                # Calculate distance between consecutive points and add to total
                gpx_dict['lat'].append(segment.points[point_idx].latitude)
                gpx_dict['lon'].append(segment.points[point_idx].longitude)
                gpx_dict['elev'].append(segment.points[point_idx].elevation)
                gpx_dict['dist'].append(segment.points[point_idx].distance_2d(segment.points[point_idx - 1]))
        
    df_route = pd.DataFrame(gpx_dict)
    df_route['dist'] = df_route['dist']/1000
    df_route['total_distance'] = df_route.dist.cumsum()
    
    return df_route

def get_route_mapbox(df, index):
    df = df.iloc[index]
    # TODO add elev
    if df.year>2021:
        df_route = get_gpx_route(df.year, index+1)
        fig = px.scatter_mapbox(df_route, lat="lat", lon="lon", hover_name='total_distance', height=600, text='elev', width=600)
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig['data'][0]['mode'] = 'lines+markers'
        return fig

    df_geo = pd.DataFrame(dict(lat=[df.stage_departure_lat, df.stage_arrival_lat],
                               lon=[df.stage_departure_lon, df.stage_arrival_lon],
                               city=[df.stage_departure, df.stage_arrival]))
    fig = px.scatter_mapbox(df_geo, lat="lat", lon="lon", hover_name='city', height=600, text='city', width=600)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig['data'][0]['mode'] = 'lines+markers'
    
    return fig

# Load Data
df = load_data("./Data_geo.csv")
displaydf = get_display_df(df, 2023)

# Build App
app = Dash(__name__)
app.layout = html.Div([
    html.H1("TDF power predictions"),
    # Overview of stages
    html.Div([
            html.Div([
                html.Label(["Year",
                dcc.Dropdown(
                    id='Year',
                    value='2023',
                    options=
                        [{'label': year, 'value': year} for year in range(1985,2024)]
                    ,clearable=False,
                )
                ]),
                dash_table.DataTable(id='Stages_table',
                                style_table={
                                    'height': 200,
                                    'overflowY': 'scroll', 'width':'100%'},
                                fixed_rows={'headers': True})
             ]),
            html.Div([
                html.Label(["Estimated profile",]),
                dcc.Graph(id='Profile_graph')
             ]),
            html.Div([
                html.Label(["Route",]),
                dcc.Graph(id='Map_graph')
             ],
            style={'width': '100%','display': 'inline-block', 'text-align':'center', 'height':'20%'}),
    ],
    style={'width': '100%','display': 'inline-block', 'text-align':'center'}),
])

@app.callback(
    [Output('Stages_table', 'data'),
     Output('Stages_table', 'columns')]
    ,[Input('Year', 'value'),]
)
def update_year(year):
    global displaydf
    displaydf = get_display_df(df, year)
    return displaydf.to_dict('records'), [ {"name": 'Year', "id": 'year'},
                        {"name": 'Stage', "id": 'stage'},
                        {"name": 'Stage Type', "id": 'stage_type'},
                        {"name": 'Leader', "id": 'gc_leader'},
                        {"name": 'Profile', "id": 'profile_icon'},
                        {"name": 'Distance (Km)', "id": 'stage_distance'},
                        {"name": 'Elevation (meters)', "id": 'stage_vertical_meters'},
                        {"name": 'Speed (Km/h)', "id": 'gc_speed'},
                        {"name": 'Power (Watts)', "id": 'power'},]
        
@app.callback(
    [Output('Profile_graph', 'figure'), 
     Output('Map_graph', 'figure')]
    ,[Input('Stages_table', 'active_cell'),
      Input('Year', 'value')]
)
def update_year(cell, _):
    global displaydf
    if cell:
        return [stage_to_profile(displaydf, cell['row']), 
                get_route_mapbox(displaydf, cell['row'])]
    else:
        return [stage_to_profile(displaydf, 0),
                get_route_mapbox(displaydf, 0)]
    


app.run_server(debug=True)


