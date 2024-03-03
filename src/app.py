from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import data_helper as dh
import visuals_helper as vh

pd.set_option('display.max_columns',50)
pd.set_option('mode.chained_assignment', None)

# Load Data
df = dh.load_data("Data_geo.csv")
global displaydf
displaydf = vh.get_display_df(df, 2023)

# Build App
app = Dash(__name__)
app.title = "TDF power"
app.layout = html.Div([
    html.H1("TDF power predictions", style={'box-shadow': 'rgba(0, 0, 0, 0.24) 0px 3px 8px', 'padding':'10px'}),
    # Overview of stages
    html.Div([
            html.Div([
                html.Label(["Stages",
                html.Hr(),
                dcc.Dropdown(
                    id='Year',
                    value='2023',
                    options=
                        [{'label': year, 'value': year} for year in range(1985,2024)]
                    ,clearable=False,
                )
                ]),
                dash_table.DataTable(id='Stages_table',
                                style_cell={'textAlign': 'left'},
                                style_table={'minWidth': '100%', "overflowY":"auto"},
                                style_header = {'display': 'none'})
             ], style={'width': '24%', 'height':'1000px', 
                       'float':'left', 'text-align': 'left', 
                       'margin': '5px', 'padding':'5px', 
                       'background-color':'white', 'box-shadow': 'rgba(0, 0, 0, 0.24) 0px 3px 8px'}),
            html.Div([
                html.Div([#right pane
                    html.Div([
                        dcc.Graph(id='Profile_graph')
                    ],
                    style={'width': '100%','display': 'inline-block', 'text-align':'center', 'height':'300px', 'margin': '5px'}),
                    html.Div([#Map/stage info and stat comparison
                        html.Div([#Map and stage info
                                html.Div(dcc.Graph(id='Map_graph'), style={'width': '40%', 'max-width':'600px', 'margin': '5px', 'float':'left'}),
                                html.Div(["Type",
                                    dcc.Dropdown(
                                        id='type',
                                        value='Estimated',
                                        clearable=False,
                                    ),
                                    html.Div(id='Stage_div', children=[
                                        dash_table.DataTable(id='stage_stats_table')
                                    ])
                                ], style={'width': '50%', 'text-align':'left', 'margin': '5px', 'float':'right'}),
                            ])
                        ,],style={'width': '100%'}),
                    html.Div(id='Overview_div', children=[
                        html.Label("Select a stat to compare")
                    ], style={'width':'100%', 'text-align':'center', 'float':'left'}),
                ], style={'width': '72%', 'float':'right',
                        'height':'1000px',
                        'margin': '5px', 'padding':'5px', 'background-color':'white',
                        'box-shadow': 'rgba(0, 0, 0, 0.24) 0px 3px 8px'},),
                
            ], )
    ],
    style={'width': '100%','display': 'inline-block', 'text-align':'center', 'background-color':'#f9f9f9'}),
])

@app.callback(
    [Output('Stages_table', 'data'),
     Output('Stages_table', 'columns'),
     Output('Stages_table', 'active_cell')]
    ,[Input('Year', 'value'),]
)
def update_year(year):
    global displaydf
    displaydf = vh.get_display_df(df, year)
    return displaydf.to_dict('records'), [{"name": 'Stage', "id": 'stage'}], {'row': 0, 'column': 0, 'column_id': 'stage'}
        
@app.callback(
    [Output('Profile_graph', 'figure'), 
     Output('Map_graph', 'figure'),
     (Output('type', 'options'), Output('type', 'value')),
     Output('Stage_div', 'children'),
     Output('stage_stats_table', 'active_cell'),]
    ,[Input('Stages_table', 'active_cell'),
      Input('Year', 'value'),
      Input('type', 'value')]
)
def update_year(cell, year, type):        
    rider = ''
    if not type in ['gpx','Estimated']:
        rider = type
        type = 'rider'
    
    if cell:
        return [vh.stage_to_profile(displaydf, cell['row'], type, rider), 
                vh.get_route_mapbox(displaydf, cell['row'], type, rider),
                dh.get_type_options(year, cell['row'], type),
                vh.get_stage_info_datatable(displaydf, cell['row']),
                {'row': 7, 'column': 0, 'column_id': 'stat'}]
    else:
        return [vh.stage_to_profile(displaydf, 0, 'Estimated'),
                vh.get_route_mapbox(displaydf, 0, 'Estimated'),
                ([{'label': 'Estimated', 'value': 'Estimated'}], 'Estimated'),
                vh.get_stage_info_datatable(displaydf, 0),
                {'row': 7, 'column': 0, 'column_id': 'stat'}]

    
@app.callback(
    Output('Overview_div', 'children'),
    Input('stage_stats_table', 'active_cell'),
    State('Stages_table', 'active_cell')
)
def update_stat_figure(stat_cell, stage_cell):        
    if stat_cell and stage_cell:
        return vh.get_stage_stats_figure(displaydf, stat_cell['row'], stage_cell['row'])
    else:
        return vh.get_stage_stats_figure(displaydf, 0, 0)


app.run_server(host='0.0.0.0', debug=True, port=8050)
