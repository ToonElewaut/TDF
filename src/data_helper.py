import pandas as pd
import power_helper as ph
import numpy as np
import gpxpy
import os
from pyworkout.parsers import tcxtools

global DATA_PATH
DATA_PATH = './Data'

def load_data(file: str):
    """Loads cycling data from a CSV file.

    Args:
    file (str): The name of the CSV file containing the cycling data.

    Returns:
    pandas.DataFrame: A DataFrame containing the cycling data.

    Raises:
    KeyError: If the specified file does not exist.
    """
    df = pd.read_csv(f'{DATA_PATH}/{file}').iloc[:,1:]
    # Riders strikes
    df = df.drop(axis=0, index=248) # 1996 stage 9
    df = df.drop(axis=0, index=234) # 1995 stage 16

    return df

def get_year_data(df: pd.DataFrame):
    """Calculates average power output for each year in the data.

    This function groups the data by year and calculates estimated power.
    Args:
    df (pandas.DataFrame): A DataFrame containing the cycling data.

    Returns:
    pandas.Series: A Series containing the average power output for each year.
    """
    # Calculate power for full tour with fixed grade
    total_climbed = df.groupby("year").stage_vertical_meters.sum()
    total_distance = df.groupby("year").stage_distance.sum()
    gc_weights = df.groupby("year").gc_weight.mean()
    gc_time = df.groupby("year").gc_stage_time.sum()
    total_grades = total_climbed/(total_distance*1000)
    velocity = (total_distance*1000)/gc_time
    year_power = ph.cycling_power(total_grades, gc_weights, velocity)
    return year_power

def get_tcx_route(year: int, stage_index: int, rider: str):
    """Loads a route for a specific stage and rider from a TCX file.
    
    Parse tcx file with pyworkout.parsers.tcxtools, used to display power data and route

    Args:
    year (int): The year of the Tour de France.
    stage_index (int): The index of the stage.
    rider (str): The name of the rider.

    Returns:
    pandas.DataFrame: A DataFrame containing the route data for the specified stage and rider.

    Raises:
    IOError: If the TCX file does not exist.
    """
    workout_data = tcxtools.TCXPandas(f'{DATA_PATH}/Routes/{year}/{rider}/stage_{stage_index}.tcx') # Create the Class Object
    df_stage = workout_data.parse()
    df_stage = df_stage.rename(columns=dict(latitude='lat', longitude='lon', altitude='elev', distance='total_distance'))

    return df_stage

def get_gpx_route(year: int, stage_index: int):
    """Loads a route for a specific stage from a GPX file.

    Parse gpx file with gpxpy, used to display route and profile

    Args:
    year (int): The year of the Tour de France.
    stage_index (int): The index of the stage.

    Returns:
    pandas.DataFrame: A DataFrame containing the route data for the specified stage.

    Raises:
    IOError: If the GPX file does not exist.
    """
    gpx_file = open(f'{DATA_PATH}/Routes/{year}/stage-{stage_index}-parcours.gpx', 'r')

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



def get_type_options(year: int, index: int, typeval: str):
    """Generates options for route data source.

    Create options based on available data files, 
    estimated only, estimated and GPX or estimated, GPX and TCX for riders.

    Args:
    year (int): Edition.
    index (int): The index of the stage (used for internal calculations).
    typeval (string): Currently selected type, deselect if not available else keep selected.

    Returns:
    list: A list of dictionaries containing label and value keys for the available 
            route data source options.
    String: Type to select
    """
    index += 1
    options = [{'label': 'Estimated', 'value': 'Estimated'}]
    if os.path.exists(f'{DATA_PATH}/Routes/{year}/stage-{index}-parcours.gpx'):
        options.append({'label': 'gpx', 'value': 'gpx'})
    for rider in [x[1] for x in os.walk(f'{DATA_PATH}/Routes/{year}/')][0]:
        if os.path.exists(f'{DATA_PATH}/Routes/{year}/{rider}/stage_{index}.tcx'):
            options.append({'label': rider, 'value': rider})
            
    if typeval in [ o['value'] for o in options]:
        return options, typeval
    else:
        return options, 'Estimated'
        