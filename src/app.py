# Import Libraries ----------------------
# Import Shiny & MongoDB
from shiny.express import input, render, ui, app, module
from shiny import reactive
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Import general use packages
import re
import math
from datetime import datetime, timedelta

# Import cosmetic package(s)
from faicons import icon_svg

# Imoprt functions from src
from config import uri
from query import *
from plots import *

# Function that @reactive.poll() will use to check whether MongoDB has been updated
def getDateTime():
    try:
        now = datetime.now()
        print('Querying Data')
        return now
            
    except Exception as e:
        print(f"Error accessing Datetime: {e}")
        return None

# Reads in the data from MongoDB reactively (CHANGE DB NAME or QUERY INTERVAL)
@reactive.poll(poll_func = getDateTime, interval_secs = 20)
def df():
    df = readData(uri,ServerApi('1'),"compression_synthetic")
    return df

# Global Settings ---------------------------
# (CHANGE DB NAME)
dataframe = readData(uri,ServerApi('1'),"compression_synthetic")
# Actuator list
actuator_list = sorted(dataframe['actuatorNumber'].unique())
# Total number of graphs to plot
num_graph = len(actuator_list)
# How many graphs to show per page
graphs_per_pg = 6
# Total number of pages
total_pages = math.ceil(num_graph / graphs_per_pg)
# Calculates the maximum X-value (time difference) among all sample numbers
maxXValue = dataframe["Time Difference"].max()

# Remove data frame to save memory
del dataframe


# SHINY DASHBOARD STARTS HERE -----------------------------

# Sets the graphs to fill up the entire page on the dashboard
ui.page_opts(fillable=True)

# Sidebar Content -------------------------------------
with ui.sidebar():
    # Real-time Graph Controls
    with ui.panel_conditional("input.tabs === 'real_time'"):
        ui.h4("Graph Variables")
        ui.input_select(
            id = "x_var",
            label = "X-axis Variable:",
            choices= ["Time Difference", "Torque", "Position (MachineCount)", "Force Signal", "Position (mm)"],
            selected='Time Difference'
        )
    
        ui.input_select(
            id = "y_var", 
            label = "Y-axis Variable:",
            choices=["Torque", "Force Signal"],
            selected='Torque'
        )
    
        ui.input_select(
            id = "y_var2",
            label= "Y-axis Variable 2:",
            choices=["Torque", "Force Signal"],
            selected='Force Signal'
        )
    
        ui.hr()

        ui.input_numeric("minX", "Minimum X Value:", 0, min=0, max=maxXValue, step = 0.01)
        ui.input_numeric("maxX", "Maximum X Value:", maxXValue, min = 0, max=maxXValue, step = 0.01)
        ui.input_action_button("applyBounds", "Apply Bounds", class_="btn-success")
        ui.input_action_button("auto_bounds", "Auto Bounds (OFF)", class_="btn-success")

        @reactive.effect
        @reactive.event(input.auto_bounds)
        def toggle_auto_bounds():
            if bounds_mode() == "auto":
                bounds_mode.set("manual")
            else:
                bounds_mode.set("auto")

        ui.hr()

        ui.h4("Page")
    
        @render.text
        def page_info():
            return f"Page {current_page()} of {total_pages}"

        ui.input_action_button("prev_page", "Previous", class_="btn-outline-primary")
        ui.input_action_button("next_page", "Next", class_="btn-outline-primary")

# Main body Content -----------------------------------------
with ui.navset_card_tab(id="tabs"):
    with ui.nav_panel("Real-time Monitoring", value="real_time"):
        
        # Use reactive.value for mutable state-
        current_page_val = reactive.value(1)

        @reactive.calc
        def current_page():
            return current_page_val()

        @reactive.effect
        @reactive.event(input.prev_page)
        def handle_prev_page():
            if current_page_val() > 1:
                current_page_val.set(current_page_val() - 1)

        @reactive.effect
        @reactive.event(input.next_page) 
        def handle_next_page():
            if current_page_val() < total_pages:
                current_page_val.set(current_page_val() + 1)

        @reactive.calc
        def current_graphs():
            """Get the 6 graphs for the current page"""
            start_idx = (current_page() - 1) * 6
            end_idx = current_page() * 6
            return actuator_list[start_idx:end_idx]
        
        # Add this reactive value to store the bounds mode
        bounds_mode = reactive.value("auto")  # "auto" or "manual"
        manual_bounds = reactive.value({'minX': 0, 'maxX': maxXValue})

        # Reactive calculation for current bounds that updates with data
        @reactive.calc
        def current_bounds():
            if bounds_mode() == "manual":
                return manual_bounds()
            else:
                # Auto mode - calculate bounds from current data
                current_data = df()
                if len(current_data) > 0:
                    max_x = current_data[input.x_var()].max()
                    min_x = input.minX()
                    return {'minX': min_x, 'maxX': max_x}
                else:
                    return {'minX': min_x, 'maxX': maxXValue}

        # Handle the Apply Bounds button
        @reactive.effect
        @reactive.event(input.applyBounds, ignore_none=False)
        def enact_bounds():
            # Update the manual bounds
            manual_bounds.set({'minX': input.minX(), 'maxX': input.maxX()})
            # Set mode to manual
            bounds_mode.set("manual")

        # Update the input boxes and their limits based on current data
        @reactive.effect
        def update_bounds_inputs():
            current_data = df()
            if len(current_data) > 0:
                max_x = current_data[input.x_var()].max()
                
                # Always update the maximum allowed value for both inputs
                ui.update_numeric("minX", max=max_x)
                ui.update_numeric("maxX", max=max_x)
                
                # Only update the actual values when in auto mode
                if bounds_mode() == "auto":
                    ui.update_numeric("maxX", value=max_x)

        # Add visual indicator for bounds mode
        @reactive.effect
        def update_auto_bounds_button():
            if bounds_mode() == "auto":
                # Update the label when Auto Bounds mode is active
                ui.update_action_button("auto_bounds", label="Auto Bounds (ON)")
            else:
                # Update the label when Auto Bounds mode is turned off
                ui.update_action_button("auto_bounds", label="Auto Bounds (OFF)")


        # Create a grid layout for the graphs
        with ui.div(class_="container-fluid"):
             # First row of graphs (3 graphs)
            with ui.div(class_="row"):
               
                with ui.div(class_="col-md-4"):
                    @render.plot
                    def graph_1():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 1:
                            fig = create_graph(data = df(), actuator = graphs[0], xVar = input.x_var(), yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    @render.plot
                    def graph_2():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 2:
                            fig = create_graph(data = df(), actuator = graphs[1], xVar = input.x_var(), yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    @render.plot
                    def graph_3():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 3:
                            fig = create_graph(data = df(), actuator = graphs[2], xVar = input.x_var(), yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
            # Second row of graphs (3 graphs)
            with ui.div(class_="row"):
                
                with ui.div(class_="col-md-4"):
                    @render.plot
                    def graph_4():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 4:
                            fig = create_graph(data = df(), actuator = graphs[3], xVar = input.x_var(), yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    @render.plot
                    def graph_5():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 5:
                            fig = create_graph(data = df(), actuator = graphs[4], xVar = input.x_var(), yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    @render.plot
                    def graph_6():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 6:
                            fig = create_graph(data = df(), actuator = graphs[5], xVar = input.x_var(), yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                    
        # Helper function to create value box content -- current threshold are hardcoded
        def get_value_box_content(actuator_index):
            y1Interval = {'y1Min': -150, 'y1Max': 150}
            y2Interval = {'y2Min': -800, 'y2Max': 1200}
            intervals = {'y1Interval': y1Interval, 'y2Interval': y2Interval}
            inputVars = {'y1Var': input.y_var(), 'y2Var': input.y_var2()}
            
            current_data = df()
            current_actuators = current_graphs()
            
            if len(current_actuators) > actuator_index:
                actuator = current_actuators[actuator_index]
                actuator_data = current_data[current_data['actuatorNumber'] == actuator]
                y1_data = actuator_data[input.y_var()].iloc[-1]
                y2_data = actuator_data[input.y_var2()].iloc[-1]
                dataDict = {'y1Data': y1_data, 'y2Data': y2_data}
                boxes = create_flagging_boxes(dataDict, intervals, inputVars, actuator)
                return ui.div(*boxes)
            return ui.div()

        # Create the flagging boxes section with explicit render functions
        with ui.layout_columns(col_widths = (2,2,2,2,2,2)):
            
            @render.ui
            def value_box_1():
                return get_value_box_content(0)
            
            @render.ui
            def value_box_2():
                return get_value_box_content(1)
            
            @render.ui
            def value_box_3():
                return get_value_box_content(2)
            
            @render.ui
            def value_box_4():
                return get_value_box_content(3)
            
            @render.ui
            def value_box_5():
                return get_value_box_content(4)
            
            @render.ui
            def value_box_6():
                return get_value_box_content(5)
        
# Helper function to create flagging boxes (place this before the main UI section)
def create_flagging_boxes(recentData, flagIntervals, variables, actuatorid):
    
    def intervalStatus(data, intervals):
        statuses = {}
        statuses['y1Status'] = intervals['y1Interval']['y1Min'] <= data['y1Data'] <= intervals['y1Interval']['y1Max']
        statuses['y2Status'] = intervals['y2Interval']['y2Min'] <= data['y2Data'] <= intervals['y2Interval']['y2Max']
        return statuses
    
    def get_icons(data, intervals):
        icons = {}
        statuses = intervalStatus(data, intervals)
        icons['y1Icon'] = icon_svg("circle-check").add_class("text-success") if statuses['y1Status'] else icon_svg("triangle-exclamation").add_class("text-danger")
        icons['y2Icon'] = icon_svg("circle-check").add_class("text-success") if statuses['y2Status'] else icon_svg("triangle-exclamation").add_class("text-danger")
        return icons
    
    def get_bottom_text(data, intervals):
        texts = {}
        statuses = intervalStatus(data, intervals)
        texts['y1BotText'] = 'Within Accepted Bounds' if statuses['y1Status'] else 'WARNING: OUTSIDE ACCEPTED BOUNDS'
        texts['y2BotText'] = 'Within Accepted Bounds' if statuses['y2Status'] else 'WARNING: OUTSIDE ACCEPTED BOUNDS'
        return texts
    
    def get_themes(data, intervals):
        themes = {}
        statuses = intervalStatus(data, intervals)
        themes['y1Theme'] = 'bg-gradient-indigo-green' if statuses['y1Status'] else 'bg-gradient-orange-red'
        themes['y2Theme'] = 'bg-gradient-indigo-green' if statuses['y2Status'] else 'bg-gradient-orange-red'
        return themes
    
    # Get all the computed values
    icons = get_icons(recentData, flagIntervals)
    texts = get_bottom_text(recentData, flagIntervals)
    themes = get_themes(recentData, flagIntervals)
    
    # Return individual value boxes that can be added to layout
    return [
        ui.value_box(
            title=f'{actuatorid} {variables["y1Var"]} Status',
            value=f'{recentData["y1Data"]:.2f}',
            showcase=icons['y1Icon'],
            theme=themes['y1Theme']
        ),
        ui.value_box(
            title=f'{actuatorid} {variables["y2Var"]} Status', 
            value=f'{recentData["y2Data"]:.2f}',
            showcase=icons['y2Icon'],
            theme=themes['y2Theme']
        )
    ]

if __name__ == "__main__":
    # Make sure to use debug=False to avoid reloader spawning a new thread
    print("Open the browser")
    app.run(debug=False, port=8000, launch_browser=True)