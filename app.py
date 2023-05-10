from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from plotly_calplot import calplot

app = Dash(__name__)
server = app.server

px.set_mapbox_access_token(open(".mapbox_token").read())

def getDateData(start_date, end_date):
        # initialize dataframe with first 1000 records
    columns_str="event_type,organization_name,facility_name,city,date_trunc_ymd(create_time),responding_organization_id,latitude,longitude"

    url = ('https://data.ny.gov/resource/ah74-pg4w.json?' +\
    '&$limit=1000' +\
    '&$offset=0' +\
    '&$select=' + columns_str +\
    '&$where=state="NY" AND date_trunc_ymd(create_time) between \"' + start_date + '\" and \"' + end_date + '\"'
    ).replace(' ', '%20')

    df = pd.read_json(url)

    #x = num_records // 1000 + 1   # too nany records. Takes 3 mins to load.
    x = 5  # number of sets of 1000

    for i in range(1, x):
        url = ('https://data.ny.gov/resource/ah74-pg4w.json?' +\
        '&$limit=1000' +\
        '&$offset=' + str(1000*i) +\
        '&$select=' + columns_str +\
        '&$where=state="NY" AND date_trunc_ymd(create_time) between \"' + start_date + '\" and \"' + end_date + '\"'
        ).replace(' ', '%20')

        df = pd.concat([df, pd.read_json(url)], axis=0)
    
    df = df.rename(columns={'date_trunc_ymd_create_time':'create_time', 'city':'location'})
    return df

def getBarChartData(start_date, end_date):
    url = ('https://data.ny.gov/resource/ah74-pg4w.json?' +\
        '&$limit=5' +\
        '&$select=event_type,count(*)' +\
        '&$group=event_type' +\
        '&$where=state="NY" AND date_trunc_ymd(create_time) between \"' + start_date + '\" and \"' + end_date + '\"' +\
        '&$order=count desc'
        ).replace(' ', '%20')
    
    return pd.read_json(url)

def initDatePicker():
    full_date = date.today()
    return date(full_date.year, full_date.month, full_date.day)

@app.callback(
        Output(component_id='vizTitle', component_property='children'),
        Input('my-date-picker-range', 'start_date'),
        Input('my-date-picker-range', 'end_date')
)
def updateTitle(start_date, end_date):
    x = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d")  # datetime object?
    x = x.strftime("%B %d, %Y")
    y = datetime.strptime(end_date, "%Y-%m-%d")  # datetime object?
    y = y.strftime("%B %d, %Y")
    return ("511 NY Events: " + str(x) + " - " + str(y))

app.layout = html.Div([
    html.H1(id="vizTitle", style={'color':'white', 'font-family':"Courier New, monospace",}),
    html.Div([
        html.Div([
            html.H2("Select a date range:", style={'color': 'white', 'font-family':"Courier New, monospace"}),
            dcc.DatePickerRange(
                id='my-date-picker-range',
                month_format='M-D-Y',
                display_format='M-D-Y',
                min_date_allowed=date(2012, 11, 6),
                max_date_allowed=date.today(),
                initial_visible_month= initDatePicker(),
                start_date=(date.today() - pd.offsets.DateOffset(years=1)),
                end_date=date.today(),
            ),
            html.Div([
                dcc.Graph(id="graph1"),
            ], style={'border':'2px black solid', 'border-radius':10, 'margin-bottom':10}),
        ], style={'backgroundColor':'black', 'display': 'flex', 'flex-direction': 'column', 'flex':'150px','padding':5}),
        html.Div([
            html.Div([
               dcc.Graph(id="graph2"), 
            ], style={'border':'2px black', 'border-radius':10}),
            html.Div([
               dcc.Graph(id="graph3"), 
            ], style={'margin-top':2}),
        ], style={'display': 'flex', 'flex-direction': 'column', 'flex':'150px', }),
    ], style={'display': 'flex', 'flex-direction': 'row',}),
], style={'backgroundColor':'black','top':0,'left':0,'position':'absolute','height':'100vh', 'width':'100vw'})

@app.callback(
        Output(component_id='graph1', component_property='figure'),
        Input('my-date-picker-range', 'start_date'),
        Input('my-date-picker-range', 'end_date')
)
def update_map(start_date, end_date):
    fig = px.scatter_mapbox(data_frame=getDateData(start_date, end_date), lat='latitude', lon='longitude', 
        opacity=0.5, 
        hover_name="event_type", 
        hover_data={"organization_name":True, 
                    "responding_organization_id":True,
                    "location":True,
                    "longitude":False, 
                    "latitude":False},
        #color="event_type",
        zoom=5,
        mapbox_style="dark"
    )
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},  # remove the white gutter between the frame and map
        height=500,  
        # hover appearance
        hoverlabel=dict( 
            bgcolor="#002054",     
            font_color="white",
            font_size=16,       
            font_family="Inter",
        ) 
    )

    return fig

@app.callback(
        Output(component_id='graph2', component_property='figure'),
        Input('my-date-picker-range', 'start_date'),
        Input('my-date-picker-range', 'end_date')
)
def update_calplot(start_date, end_date):
    test2 = getDateData(start_date, end_date)
    test2 = test2.groupby(["create_time"])["create_time"].count()
    create_time_df = pd.DataFrame(test2.index, columns=["create_time"])
    num_events_df = pd.DataFrame(test2.values, columns=["num_events"])
    df = pd.concat([create_time_df, num_events_df], axis=1)
    df["create_time"] = pd.to_datetime(df["create_time"])
    calplot_fig = calplot(df, x="create_time", y="num_events", dark_theme=True, title="Events Heatmap",colorscale="blues")
    return calplot_fig

@app.callback(
    Output(component_id='graph3', component_property='figure'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
)
def update_barchart(start_date, end_date):
    df = getBarChartData(start_date, end_date)
    fig = px.bar(df, x='event_type', y='count', title="Top 5 Event Types")

    fig.update_layout(
        paper_bgcolor="#363636",
        plot_bgcolor="#363636",
        font_color="white",
        height=400,
        font=dict(
            family="Courier New, monospace",
        )
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
    