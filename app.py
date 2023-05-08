from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from datetime import date
from plotly_calplot import calplot

app = Dash(__name__)
server = app.server

px.set_mapbox_access_token(open(".mapbox_token").read())

def getDateData(start_date, end_date):
    url = ('https://data.ny.gov/resource/ah74-pg4w.json?' +\
        '$limit=200&$offset=0' +\
        '&$select=*' +\
        '&$where=date_trunc_ymd(create_time) between \"' + start_date + '\" and \"' + end_date + '\"'
        ).replace(' ', '%20')
    test = pd.read_json(url)
    return test

def initDatePicker():
    url = ('https://data.ny.gov/resource/ah74-pg4w.json?' +\
    '&$select=date_trunc_ymd(max(create_time)) as create_time'
    ).replace(' ', '%20')
    full_date=pd.read_json(url).create_time.item()
    return date(full_date.year, full_date.month, full_date.day)

my_url='sales_data_sample.csv'
df = pd.read_csv(my_url, encoding_errors='ignore')
df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
pl1 = calplot(df, x="ORDERDATE", y="SALES", dark_theme=True)
# The only requirement for you to use this plot is that you have 
# a Pandas dataframe with a date column (see pandas to_datetime docs) 
# and a value column which will be used as the value we’ll plot.

app.layout = html.Div([
    html.Div([
        dcc.Graph(id="graph1"),
        dcc.DatePickerRange(
            id='my-date-picker-range',
            month_format='MMM Do, YYYY',
            display_format='MMM Do, YYYY',
            min_date_allowed=date(2012, 11, 6),
            max_date_allowed=date(2020, 4, 20),
            initial_visible_month= initDatePicker(),#date(2020, 4, 20),
            start_date=date(2020, 1, 20),
            end_date=date(2020, 4, 20)
        ),
        dcc.Graph(id="graph2", figure=pl1),
    ], style={'padding': 10, 'flex': 1}),
], style={'display': 'flex', 'flex-direction': 'row'})

@app.callback(
        Output(component_id='graph1', component_property='figure'),
        Input('my-date-picker-range', 'start_date'),
        Input('my-date-picker-range', 'end_date')
)
def update_map(start_date, end_date):
    fig = px.scatter_mapbox(data_frame=getDateData(start_date, end_date), lat='latitude', lon='longitude', 
        opacity=0.5, 
        hover_name="event_type", 
        hover_data=["organization_name","state", "county", "create_time"], 
        zoom=5,
        mapbox_style="dark"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},  # remove the white gutter between the frame and map
            # hover appearance
            hoverlabel=dict( 
            bgcolor="white",     # white background
            font_size=16,        # label font size
            font_family="Inter") # label font
    )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
    