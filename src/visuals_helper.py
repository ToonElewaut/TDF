import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import power_helper as ph
import numpy as np
import data_helper as dh
from dash import dash_table, dcc, html


def get_random_scaled_segments(goal: int, segments: int, flat_finish = False, arrival_elev = 0, min = 1, max = 25, distance = False):
    """Generates a list of scaled random segments with a target sum.

    This function generates a list of `segments` random integers between `min` and
    `max`. It then scales these numbers proportionally to ensure their sum reaches
    the target `goal`. The scaling factor is calculated by dividing the `goal` by
    the initial sum of the random numbers.

    Optionally, the function can handle distance and elevation profiles separately.
    If `distance` is True, the first and last segments are set to 0 to ensure a
    flat start and finish. If `flat_finish` is True, the last segment is set to 0
    to simulate a flat finish, and the segment before the last is adjusted to
    maintain the target sum. Otherwise, the last two segments are adjusted to
    simulate an uphill finish with a negative elevation gain for the last segment.

    Args:
    goal (int): The target sum for the scaled segments.
    segments (int): The number of segments to generate.
    flat_finish (bool, optional): Simulate a flat finish by setting the last segment to 0. Defaults to False.
    arrival_elev (int, optional): The elevation at the arrival point. Defaults to 0.
    min (int, optional): The minimum value for the random segments. Defaults to 1.
    max (int, optional): The maximum value for the random segments. Defaults to 25.
    distance (bool, optional): If True, handle distance profile separately. Defaults to False.

    Returns:
    list: A list of scaled random segments.
    """
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

def profile_xy(stage_distance: int, stage_vertical_meters: int, peaks=4, flat_finish=False, departure_elev=0, arrival_elev=0):
    """Generates x and y data for a stage profile plot.

    Generate x and y values for displaying an randomly estimated elevation profile
    based on the departure_elevation, arrival_elevation and meters climbed. Peaks and
    flatfinish is used based on the stage_profile to more closely represent the type of stage.
    
    Args:
    stage_distance (int): The total distance of the stage.
    stage_vertical_meters (int): The total vertical meters climbed in the stage.
    peaks (int, optional): The number of peaks to simulate in the profile. Defaults to 4.
    flat_finish (bool, optional): Simulate a flat finish. Defaults to False.
    departure_elev (int, optional): The elevation at the departure point. Defaults to 0.
    arrival_elev (int, optional): The elevation at the arrival point. Defaults to 0.

    Returns:
    tuple: A tuple containing two lists, the first representing the x-axis data (distance)
            and the second representing the y-axis data (elevation).
    """   
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

def stage_to_profile(display_df: pd.DataFrame, index: int, type: str, rider ='Kuss'):
    """Generates a stage profile plot based on data or estimated profile.

    This function creates a stage profile plot using either actual route data or an
    estimated profile. It takes a DataFrame (`display_df`) containing stage information,
    the index of the stage (`index`), the type of profile data to use (`type`), and
    an optional rider name (`rider`) for rider-specific TCX route data.

    If `type` is 'gpx', the function retrieves the route data from a GPX file and
    creates a filled area plot using Plotly Express (`px.area`).
    If `type` is 'rider', the function retrieves the route data from a TCX file for
    the specified rider and creates a scatter plot colored by power using Plotly Express
    (`px.scatter`).

    Otherwise, the function estimates the profile using `profile_xy` based on
    information in `display_df` such as stage distance, total vertical meters, profile
    icon
    
    Args:
    display_df (pandas.Dataframe): Dataframe containing stage info.
    index (int): Index of selected stage.
    type (str): Type to display 'Estimated', 'GPX' or riderspecific 'TCX'
    rider (str, optional): Rider name for TCX file. Defaults to 'Kuss'.

    Returns:
    plotly.Figure: A Figure containing the stage profile.
    """
    if type == 'gpx':
        df_route = dh.get_gpx_route(display_df.iloc[index].year, index+1)
        fig = px.area(df_route, x='total_distance', y='elev', line_shape='linear', color_discrete_sequence=['ForestGreen', 'Aquamarine'], height=300)
        fig.update_layout(plot_bgcolor='white', yaxis_title=None, xaxis_title=None, transition_duration=500, transition_easing='cubic-in-out',  title='GPX profile')
    
        fig.update_xaxes(range = [0,display_df.stage_distance.max()], showgrid=False)
        fig.update_yaxes(range = [ 0,2850 ], showgrid=False)
        return fig
    if type == 'rider':
        df_route = dh.get_tcx_route(display_df.iloc[index].year, index+1, rider)
        df_route.total_distance = df_route.total_distance/1000
        fig = px.scatter(df_route, x='total_distance', y='elev', color='power', range_color=[0,300], height=300, title='TCX profile')
        fig.update_layout(plot_bgcolor='white', yaxis_title=None, xaxis_title=None, transition_duration=500, transition_easing='cubic-in-out')

        fig.update_xaxes(range = [0,display_df.stage_distance.max()], showgrid=False)
        fig.update_yaxes(range = [ 0,2850 ], showgrid=False)
        return fig

    peaks, flat = {'flat':(40, True), 
                        'Hills, flat finish': (20, True), 
                        'Hills, uphill finish': (20, False), 
                        'Mountains, flat finish': (7, True), 
                        'Mountains, uphill finish':(7, False)}.get(display_df.iloc[index].profile_icon)

    x, y = profile_xy(display_df.iloc[index].stage_distance, 
                        display_df.iloc[index].stage_vertical_meters, 
                        peaks, flat, 
                        display_df.iloc[index].stage_departure_elevs, 
                        display_df.iloc[index].stage_arrival_elevs)
    fig = px.area(x=x, y=np.add(y,50), line_shape='linear', color_discrete_sequence=['ForestGreen', 'Aquamarine'], height=300)
    fig.update_layout(plot_bgcolor='white', yaxis_title=None, xaxis_title=None, transition_duration=500, transition_easing='cubic-in-out',  title='Estimated profile')

    fig.update_xaxes(range = [0,display_df.stage_distance.max()], showgrid=False)
    fig.update_yaxes(range = [ 0,2850 ], showgrid=False)
    return fig

def get_display_df(df: pd.DataFrame, year: int):
    """Filters a DataFrame for display.

    This function selects and formats relevant columns from a DataFrame containing
    cycling stage data for a specific year.

    Args:
      df (pandas.DataFrame): A DataFrame containing cycling stage data. 
      year (int): Edition year.

    Returns:
      pandas.DataFrame: A DataFrame containing formatted data for display.
    """
    display_df = df[['year', 'stage_departure', 'stage_arrival', 
                     'stage_type', 'gc_leader', 'profile_icon', 
                     'stage_distance', 'stage_vertical_meters', 
                     'gc_speed', 'power', 
                     'stage_departure_lat', 'stage_departure_lon',
                     'stage_arrival_lat', 'stage_arrival_lon',
                     'stage_departure_elevs', 'stage_arrival_elevs', 
                     'stage_winner_time_str', 'stage_winner', 'stage_grade', 'gc_weight']]
    # Replace values for display
    display_df = display_df[display_df.year == int(year)]
    display_df.profile_icon = display_df.profile_icon.replace({'p1':'flat', 'p2':'Hills, flat finish', 'p3': 'Hills, uphill finish',
                         'p4':'Mountains, flat finish', 'p5':'Mountains, uphill finish'})
    display_df.stage_type = display_df.stage_type.replace({'RR':'Race', 'ITT':'TT'})
    display_df.gc_speed = display_df.gc_speed * 3.6
    display_df['stage'] = display_df.stage_departure + '-' + display_df.stage_arrival
    display_df = display_df.round(1)
    return display_df

def get_route_mapbox(df: pd.DataFrame, index: int, type: str, rider='Kuss'):
    """Generates a route map on a Mapbox.

    This function creates a Plotly Express figure showing the route of a cycling
    stage on a Mapbox map. It can handle different route data sources:

      - 'gpx': Uses a GPX file containing route information for the stage.
      - 'rider': Uses a TCX file containing the route for a specific rider in the stage.
      - 'stage' (or any other invalid type): Uses the stage departure and arrival locations to draw a simple line between them.

    Args:
      df (pandas.DataFrame): A DataFrame containing stage data.
      index (int): The index of the stage in the DataFrame.
      type (str): The type of route data to use: "gpx", "rider", or "stage" (or any valid profile icon code).
      rider (str, optional): The name of the rider for route data (if type is "rider").
          Defaults to "Kuss".

    Returns:
      plotly.graph_objects.Figure: A Plotly Express figure showing the route map.

    Raises:
      ValueError: If the type is not a valid option.
    """
    df = df.iloc[index]
    if type == 'gpx':
        df_route = dh.get_gpx_route(df.year, index+1)
        fig = px.scatter_mapbox(df_route, lat="lat", lon="lon", hover_name='total_distance', text='elev')
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig['data'][0]['mode'] = 'lines+markers'
        return fig
    
    if type == 'rider':
        df_route = dh.get_tcx_route(df.year, index+1, rider)
        fig = px.scatter_mapbox(df_route, lat="lat", lon="lon", hover_name='total_distance', text='elev', color='power', range_color=[0,300])
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.update_coloraxes(showscale=False)
        fig['data'][0]['mode'] = 'lines+markers'
        return fig
    
    df_geo = pd.DataFrame(dict(lat=[df.stage_departure_lat, df.stage_arrival_lat],
                                lon=[df.stage_departure_lon, df.stage_arrival_lon],
                                city=[df.stage_departure, df.stage_arrival]))
    fig = px.scatter_mapbox(df_geo, lat="lat", lon="lon", hover_name='city', text='city')
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig['data'][0]['mode'] = 'lines+markers'
        
    return fig

def get_stage_info_datatable(displaydf: pd.DataFrame, index: int):
    """Generates a DataTable component to display stage information.

    Args:
        displaydf (pd.DataFrame): DataFrame containing stage information.
        index (int): Index of the stage to display information for.

    Returns:
        dash.DataTable: A DataTable component displaying stage information.
    """
    stats = ['year', 'Departure', 'Arrival', 'Type', 'Profile', 'Stage winner', 'GC leader', 'Time',  'Distance', 'Vertical meters', 'Speed', 'Power']
    vals = ['year', 'stage_departure', 'stage_arrival', 'stage_type', 'profile_icon',
            'stage_winner', 'gc_leader', 'stage_winner_time_str', 'stage_distance', 'stage_vertical_meters', 'gc_speed', 'power']
    displaydf.power = round(ph.cycling_power(displaydf.iloc[index].stage_grade, 
                                       displaydf.iloc[index].gc_weight, 
                                       displaydf.iloc[index].gc_speed/3.6), 2)
    return dash_table.DataTable(id='stage_stats_table',
                                columns=[{"name": 'stat', "id": 'stat'}, {"name": 'value', "id": 'value'}],
                                data= [{'stat':stat, 'value':val} 
                                    for stat, val in 
                                    zip(stats, 
                                        displaydf[vals].iloc[index].reset_index()[displaydf.iloc[index:].index[0]].values)],
                                style_table={
                                        'height': '400px',
                                        'overflowY': 'scroll', 'width':'100%'},
                                style_header = {'display': 'none'},
                                style_cell_conditional=[
                                {'if': {'column_id': 'stat'},
                                'textAlign': 'left'}])
    
    
    
def to_seconds(time):
    h, m, s = time.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def get_stage_stats_figure(displaydf: pd.DataFrame, index: int, current_stage_index: int):
    """Generates a Figure component to compare stage information to other stages.

    Args:
        displaydf (pd.DataFrame): DataFrame containing stage information.
        index (int): Index of the stage to display information for.

    Returns:
        plotly.Figure: A graph displaying stage information.
    """
    stats = ['year', 'Departure', 'Arrival', 'Type', 'Profile', 'Stage winner', 'GC leader', 'Time',  'Distance', 'Vertical meters', 'Speed', 'Power']
    vals = ['year', 'stage_departure', 'stage_arrival', 'stage_type', 'profile_icon',
            'stage_winner', 'gc_leader', 'stage_winner_time_str', 'stage_distance', 'stage_vertical_meters', 'gc_speed', 'power']
    displaydf.power = round(ph.cycling_power(displaydf.stage_grade, 
                                       displaydf.gc_weight, 
                                       displaydf.gc_speed/3.6), 2)
    displaydf = displaydf.reset_index(drop=True)
    displaydf.stage_winner_time_str = displaydf.stage_winner_time_str.apply(lambda x: to_seconds(x)) / 3600
    if vals[index] in ['stage_winner_time_str', 'stage_distance', 'stage_vertical_meters', 'gc_speed', 'power']:
        fig = px.scatter(displaydf, y=vals[index], hover_data='stage', labels=stats[index], height=200)
        fig.update_layout(plot_bgcolor='white', yaxis_title=stats[index], xaxis_title=None, transition_duration=500, transition_easing='cubic-in-out')
        fig.add_trace(go.Scatter(
                x=[current_stage_index],
                y=[displaydf.loc[current_stage_index, vals[index]]],
                mode="markers",
                marker=dict(
                    color="red",
                    size=10,
                ),
                name="Current stage"
            )
)
        fig.update_xaxes(showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False)
        return [dcc.Graph(figure=fig, style={'width':'100%', 'margin':'5px'})]
    
    return [html.Label("Select a stat to compare")]