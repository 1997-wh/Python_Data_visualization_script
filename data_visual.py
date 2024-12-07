import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
from flask import Flask, send_file
import threading
import time
import random
import io

# Initialize Flask app
server = Flask(__name__)

# Load initial dataset from CSV
df = pd.read_csv('sample_data_visualization.csv')

# Initialize Dash app
app = dash.Dash(__name__, server=server)
app.title = "Interactive Data Visualization Dashboard"

# Store for annotations
annotations_store = []

# App layout
app.layout = html.Div(id="main-container", children=[
    dcc.Store(id="theme-store", data="light"),
    html.H1("Interactive Data Visualization Dashboard", id="dashboard-title", style={"textAlign": "center"}),
    
    html.Div([
        html.Label("Filter Data by Value Range:"),
        dcc.RangeSlider(
            id="value-range-slider",
            min=df['Value'].min(),
            max=df['Value'].max(),
            step=5,
            marks={i: str(i) for i in range(int(df['Value'].min()), int(df['Value'].max())+1, 10)},
            value=[df['Value'].min(), df['Value'].max()]
        ),
    ], style={"margin": "20px"}),

    html.Div([
        html.Label("Select Category:"),
        dcc.Dropdown(
            id="category-dropdown",
            options=[{"label": cat, "value": cat} for cat in df['Category'].unique()],
            value=df['Category'].unique()[0],
            clearable=False
        )
    ], style={"margin": "20px"}),

    html.Div([
        html.Label("Select Region:"),
        dcc.Dropdown(
            id="region-dropdown",
            options=[{"label": reg, "value": reg} for reg in df['Region'].unique()],
            value=df['Region'].unique()[0],
            clearable=False
        )
    ], style={"margin": "20px"}),

    html.Div([
        html.Label("Summary Statistics:"),
        html.Div(id="summary-stats", style={"margin": "10px", "fontWeight": "bold"}),
    ]),

    html.Div([
        html.Label("Select Categories to Display:"),
        dcc.Checklist(
            id="category-toggle",
            options=[{"label": cat, "value": cat} for cat in df['Category'].unique()],
            value=df['Category'].unique(),
            inline=True,
            style={"marginBottom": "10px"}
        )
    ]),

    dcc.Graph(id="main-line-chart", config={"scrollZoom": True}, style={"marginBottom": "20px"}),

    html.Div([
        dcc.Graph(id="line-chart-a", config={"scrollZoom": True}, style={"display": "inline-block", "width": "32%"}),
        dcc.Graph(id="line-chart-b", config={"scrollZoom": True}, style={"display": "inline-block", "width": "32%"}),
        dcc.Graph(id="line-chart-c", config={"scrollZoom": True}, style={"display": "inline-block", "width": "32%"}),
    ]),

    html.Div([
        html.Label("Interactive Data Table:"),
        dcc.Loading(
            id="loading-table",
            children=[
                html.Div(id="data-table-container")
            ],
            type="circle"
        )
    ], style={"margin": "20px"}),

    html.Div([
        html.Label("Annotations:"),
        html.Div([
            dcc.Input(
                id="annotation-text",
                type="text",
                placeholder="Enter annotation",
                style={"marginRight": "10px"}
            ),
            html.Button("Add Annotation", id="add-annotation-btn"),
            html.Button("Delete Annotations", id="delete-annotations-btn", style={"marginLeft": "10px"})
        ], style={"margin": "10px"}),
        html.Div(id="selected-point", style={"margin": "10px", "fontWeight": "bold"}),
        dcc.Graph(id="annotated-line-chart", config={"scrollZoom": True})
    ]),

    html.Div([
        html.Button("Download Data", id="download-btn"),
        dcc.Download(id="download-dataframe-csv")
    ], style={"margin": "20px"}),

    dcc.Interval(
        id="interval-component",
        interval=5000,  # Update every 5 seconds
        n_intervals=0
    )
], style={"padding": "0", "margin": "0", "height": "100vh", "width": "100vw", "backgroundColor": "#ffffff"})

# Callback for downloading data
@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-btn", "n_clicks")]
)
def download_data(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return dcc.send_data_frame(df.to_csv, "real_time_data.csv")

# Callback for updating summary statistics
@app.callback(
    Output("summary-stats", "children"),
    [Input("value-range-slider", "value"), Input("category-dropdown", "value"), Input("region-dropdown", "value"), Input("interval-component", "n_intervals")]
)
def update_summary(value_range, selected_category, selected_region, n):
    filtered_df = df[(df["Value"] >= value_range[0]) & (df["Value"] <= value_range[1]) & (df["Category"] == selected_category) & (df["Region"] == selected_region)]
    if not filtered_df.empty:
        mean_val = filtered_df["Value"].mean()
        max_val = filtered_df["Value"].max()
        min_val = filtered_df["Value"].min()
        return f"Mean: {mean_val:.2f}, Max: {max_val}, Min: {min_val}"
    else:
        return "No data available for the selected filters."

# Callback for updating the main line chart and individual line charts
@app.callback(
    [Output("main-line-chart", "figure"),
     Output("line-chart-a", "figure"),
     Output("line-chart-b", "figure"),
     Output("line-chart-c", "figure")],
    [Input("value-range-slider", "value"), Input("region-dropdown", "value"), Input("interval-component", "n_intervals"), Input("category-toggle", "value")]
)
def update_charts(value_range, selected_region, n, selected_categories):
    filtered_df = df[(df["Value"] >= value_range[0]) & (df["Value"] <= value_range[1]) & (df["Region"] == selected_region)]
    filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]

    main_line_chart = px.line(
        filtered_df,
        x="Timestamp",
        y="Value",
        color="Category",
        title="Overall Trends by Selected Categories",
        labels={"Value": "Value", "Timestamp": "Timestamp", "Category": "Category"}
    ) if not filtered_df.empty else px.line(title="No Data Available")

    line_chart_a = px.line(
        filtered_df[filtered_df["Category"] == "A"],
        x="Timestamp",
        y="Value",
        title="Category A",
        labels={"Value": "Value", "Timestamp": "Timestamp"}
    ) if not filtered_df.empty else px.line(title="No Data Available")

    line_chart_b = px.line(
        filtered_df[filtered_df["Category"] == "B"],
        x="Timestamp",
        y="Value",
        title="Category B",
        labels={"Value": "Value", "Timestamp": "Timestamp"}
    ) if not filtered_df.empty else px.line(title="No Data Available")

    line_chart_c = px.line(
        filtered_df[filtered_df["Category"] == "C"],
        x="Timestamp",
        y="Value",
        title="Category C",
        labels={"Value": "Value", "Timestamp": "Timestamp"}
    ) if not filtered_df.empty else px.line(title="No Data Available")

    return main_line_chart, line_chart_a, line_chart_b, line_chart_c

# Callback for updating graphs and managing annotations
@app.callback(
    [Output("selected-point", "children"), Output("annotated-line-chart", "figure")],
    [Input("annotated-line-chart", "clickData"), Input("add-annotation-btn", "n_clicks"), Input("delete-annotations-btn", "n_clicks")],
    [State("annotation-text", "value")]
)
def handle_annotation(click_data, add_clicks, delete_clicks, annotation_text):
    global annotations_store
    ctx = dash.callback_context
    selected_point_info = "Click on the chart to select a point for annotation."

    # Check if there's clickData
    if click_data and "points" in click_data:
        selected_point = click_data["points"][0]
        selected_x = selected_point["x"]
        selected_y = selected_point["y"]
        selected_point_info = f"Selected Point - X: {selected_x}, Y: {selected_y}"

        if ctx.triggered and "add-annotation-btn" in ctx.triggered[0]["prop_id"]:
            if annotation_text:
                new_annotation = {
                    "x": selected_x,
                    "y": selected_y,
                    "text": annotation_text
                }
                annotations_store.append(new_annotation)

    if ctx.triggered and "delete-annotations-btn" in ctx.triggered[0]["prop_id"]:
        annotations_store = []

    # Recreate figure
    annotated_chart = px.line(
        df,
        x="Timestamp",
        y="Value",
        title="Annotated Line Chart",
        labels={"Value": "Value", "Timestamp": "Timestamp"}
    )
    for annotation in annotations_store:
        annotated_chart.add_annotation(
            x=annotation["x"],
            y=annotation["y"],
            text=annotation["text"],
            showarrow=True,
            arrowhead=1
        )

    return selected_point_info, annotated_chart

# Callback for rendering data table
@app.callback(
    Output("data-table-container", "children"),
    [Input("value-range-slider", "value"), Input("category-dropdown", "value"), Input("region-dropdown", "value"), Input("interval-component", "n_intervals")]
)
def update_data_table(value_range, selected_category, selected_region, n):
    filtered_df = df[(df["Value"] >= value_range[0]) & (df["Value"] <= value_range[1]) & (df["Category"] == selected_category) & (df["Region"] == selected_region)]
    if not filtered_df.empty:
        return dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in filtered_df.columns],
            data=filtered_df.to_dict("records"),
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "5px"},
            style_header={"fontWeight": "bold"}
        )
    else:
        return html.Div("No data available for the selected filters.", style={"textAlign": "center", "margin": "20px"})

if __name__ == "__main__":
    app.run_server(debug=True)
