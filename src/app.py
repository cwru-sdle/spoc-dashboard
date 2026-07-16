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
import pandas as pd
import matplotlib.pyplot as plt

# Import cosmetic package(s)
from faicons import icon_svg

# Imoprt functions from src
from config import uri
from query import *
from plots import *
from utils import *

# Polls MongoDB for the latest timeseries data.
@reactive.poll(poll_func = getDateTime, interval_secs = 20)
def df():
    """
    Poll MongoDB for updated timeseries data.

    This reactive function refreshes the dataset every 20 seconds
    to keep the real-time dashboard up to date.

    Returns:
        pd.DataFrame: Latest timeseries data formatted for plotting.
    """
    #df = readData(uri,ServerApi('1'),"compression_synthetic")
    df = readData(uri,ServerApi('1'),"Compression-SPOC-Project", "compression-set-timeseries")
    return df

# Global Settings ---------------------------
# (CHANGE DB NAME)
#dataframe = readData(uri,ServerApi('1'),"compression_synthetic")
dataframe = readData(uri,ServerApi('1'),"Compression-SPOC-Project", "compression-set-timeseries")
# Actuator list
actuator_list = sorted(dataframe['actuatorNumber'].unique())
# Total number of graphs to plot
num_graph = len(actuator_list)
# How many graphs to show per page
graphs_per_pg = 6
# Total number of pages
total_pages = math.ceil(num_graph / graphs_per_pg)

# Remove data frame to save memory
del dataframe

# Metadata loaded once at startup (non-reactive)
part_metadata_df = read_metadata_df(
    uri, ServerApi("1"), "Compression-SPOC-Project", "part-metadata"
)
batch_metadata_df = read_metadata_df(
    uri, ServerApi("1"), "Compression-SPOC-Project", "batch-metadata"
)

# SHINY DASHBOARD UI STARTS HERE -----------------------------

# Sets the graphs to fill up the entire page on the dashboard
ui.page_opts(fillable=True)

# Sidebar Content -------------------------------------
with ui.sidebar():
    # Real-time Graph Controls
    with ui.panel_conditional("input.tabs === 'real_time'"):
        ui.h4("Graph Variables")
    
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

        ui.h4("Time Window")

        ui.input_select(
            id="time_window",
            label="Display Range:",
            choices={
                "live_1h": "Live - Last 1 Hour",
                "15m": "Last 15 Minutes",
                "30m": "Last 30 Minutes",
                "1h": "Last 1 Hour",
                "custom": "Custom Range",
            },
            selected="live_1h"
        )

        ui.input_text("start_time", "Start Time (YYYY-MM-DD HH:MM)", placeholder="YYYY-MM-DD HH:MM")
        ui.input_text("end_time", "End Time (YYYY-MM-DD HH:MM)", placeholder="YYYY-MM-DD HH:MM")
        ui.input_action_button("apply_time_window", "Apply Time Window", class_="btn-success")

        ui.hr()

        ui.h4("Page")
    
        # Shows the current page number in the sidebar.
        @render.text
        def page_info():
            return f"Page {current_page()} of {total_pages}"

        ui.input_action_button("prev_page", "Previous", class_="btn-outline-primary")
        ui.input_action_button("next_page", "Next", class_="btn-outline-primary")

    # Metadata Controls
    with ui.panel_conditional("input.tabs === 'metadata'"):
        ui.h4("Chart Controls")

        ui.input_select(
            id="metadata_group_by",
            label="Group by:",
            choices={
                "BatchID": "Batch ID",
                "CuringType": "Curing Type",
                "PartShape": "Part Shape",
                "PolymerType": "Polymer Type",
                "Nanoparticle": "Nanoparticle",
            },
            selected="BatchID"
        )

        ui.input_select(
            id="metadata_y_metric",
            label="Metric:",
            choices={
                "avg_thickness": "Average Thickness",
                "avg_curing_temp": "Average Curing Temperature",
                "avg_test_duration": "Average Test Duration",
                "avg_strain": "Average Strain",
                "count_parts": "Count of Parts",
            },
            selected="avg_thickness"
        )

        ui.hr()
        ui.h4("Table Filters")

        batch_id_choices = sorted(batch_metadata_df["BatchID"].dropna().astype(str).unique().tolist()) \
            if not batch_metadata_df.empty and "BatchID" in batch_metadata_df.columns else []

        part_id_choices = sorted(part_metadata_df["PartID"].dropna().astype(str).unique().tolist()) \
            if not part_metadata_df.empty and "PartID" in part_metadata_df.columns else []

        curing_type_choices = sorted(part_metadata_df["CuringType"].dropna().astype(str).unique().tolist()) \
            if not part_metadata_df.empty and "CuringType" in part_metadata_df.columns else []

        part_shape_choices = sorted(part_metadata_df["PartShape"].dropna().astype(str).unique().tolist()) \
            if not part_metadata_df.empty and "PartShape" in part_metadata_df.columns else []

        polymer_type_choices = sorted(batch_metadata_df["PolymerType"].dropna().astype(str).unique().tolist()) \
            if not batch_metadata_df.empty and "PolymerType" in batch_metadata_df.columns else []

        ui.input_selectize(
            id="filter_batch_id",
            label="Batch ID",
            choices=batch_id_choices,
            selected=None,
            multiple=True,
            remove_button=True,
            options={"placeholder": "Search batch IDs..."}
        )

        ui.input_selectize(
            id="filter_part_id",
            label="Part ID",
            choices=part_id_choices,
            selected=None,
            multiple=True,
            remove_button=True,
            options={"placeholder": "Search part IDs..."}
        )

        ui.input_selectize(
            id="filter_curing_type",
            label="Curing Type",
            choices=curing_type_choices,
            selected=None,
            multiple=True,
            remove_button=True,
            options={"placeholder": "Search curing types..."}
        )

        ui.input_selectize(
            id="filter_part_shape",
            label="Part Shape",
            choices=part_shape_choices,
            selected=None,
            multiple=True,
            remove_button=True,
            options={"placeholder": "Search part shapes..."}
        )

        ui.input_selectize(
            id="filter_polymer_type",
            label="Polymer Type",
            choices=polymer_type_choices,
            selected=None,
            multiple=True,
            remove_button=True,
            options={"placeholder": "Search polymer types..."}
        )

        ui.input_action_button(
            "reset_metadata_filters",
            "Reset Filters",
            class_="btn-outline-secondary"
        )

# Main body Content -----------------------------------------
with ui.navset_card_tab(id="tabs"):
    # Tab 1: Real-time Monitoring
    with ui.nav_panel("Real-time Monitoring", value="real_time"):
        
        # Use reactive.value for mutable state-
        current_page_val = reactive.value(1)

        # Returns the current page index.
        @reactive.calc
        def current_page():
            return current_page_val()

        # Moves to the previous page when the button is clicked.
        @reactive.effect
        @reactive.event(input.prev_page)
        def handle_prev_page():
            if current_page_val() > 1:
                current_page_val.set(current_page_val() - 1)

        # Moves to the next page when the button is clicked.
        @reactive.effect
        @reactive.event(input.next_page) 
        def handle_next_page():
            if current_page_val() < total_pages:
                current_page_val.set(current_page_val() + 1)

        @reactive.calc
        def current_graphs():
            """
            Determine which actuator IDs should be displayed on the current page.

            Returns:
                list: Subset of actuator IDs for the current page.
            """
            start_idx = (current_page() - 1) * 6
            end_idx = current_page() * 6
            return actuator_list[start_idx:end_idx]
        
        manual_time_window = reactive.value({"start": None, "end": None})
        time_window_mode = reactive.value("live_1h")


        @reactive.effect
        @reactive.event(input.apply_time_window)
        def apply_time_window():
            """
            Update the active time window based on user input.

            Supports predefined ranges (e.g., last 15 min, 1 hour) and
            custom start/end datetime values.
            """
            selected = input.time_window()

            if selected == "custom":
                start = parse_datetime_input(input.start_time())
                end = parse_datetime_input(input.end_time())

                if start is not None and end is not None:
                    manual_time_window.set({
                        "start": start,
                        "end": end
                    })

            time_window_mode.set(selected)


        @reactive.calc
        def current_bounds():
            """
            Compute the active x-axis time range for plots.

            Returns:
                dict: Dictionary with minX and maxX timestamps.
            """
            current_data = df()

            if len(current_data) == 0:
                return {"minX": None, "maxX": None}

            current_data = current_data.dropna(subset=["DateTime"]).sort_values("DateTime")
            latest_time = current_data["DateTime"].max()

            mode = time_window_mode()

            if mode == "live_1h":
                return {
                    "minX": latest_time - timedelta(hours=1),
                    "maxX": latest_time
                }

            elif mode == "15m":
                return {
                    "minX": latest_time - timedelta(minutes=15),
                    "maxX": latest_time
                }

            elif mode == "30m":
                return {
                    "minX": latest_time - timedelta(minutes=30),
                    "maxX": latest_time
                }

            elif mode == "1h":
                return {
                    "minX": latest_time - timedelta(hours=1),
                    "maxX": latest_time
                }

            elif mode == "custom":
                window = manual_time_window()
                return {
                    "minX": window["start"],
                    "maxX": window["end"]
                }

            return {
                "minX": latest_time - timedelta(hours=1),
                "maxX": latest_time
            }


        # Create a grid layout for the graphs
        with ui.div(class_="container-fluid"):
             # First row of graphs (3 graphs)
            with ui.div(class_="row"):
               
                with ui.div(class_="col-md-4"):
                    # Renders the first real-time chart on the page.
                    @render.plot
                    def graph_1():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 1:
                            fig = create_graph(data = df(), actuator = graphs[0], yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    # Renders the second real-time chart on the page.
                    @render.plot
                    def graph_2():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 2:
                            fig = create_graph(data = df(), actuator = graphs[1], yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    # Renders the third real-time chart on the page.
                    @render.plot
                    def graph_3():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 3:
                            fig = create_graph(data = df(), actuator = graphs[2], yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
            # Second row of graphs (3 graphs)
            with ui.div(class_="row"):
                
                with ui.div(class_="col-md-4"):
                    # Renders the fourth real-time chart on the page.
                    @render.plot
                    def graph_4():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 4:
                            fig = create_graph(data = df(), actuator = graphs[3], yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    # Renders the fifth real-time chart on the page.
                    @render.plot
                    def graph_5():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 5:
                            fig = create_graph(data = df(), actuator = graphs[4], yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                
                with ui.div(class_="col-md-4"):
                    # Renders the sixth real-time chart on the page.
                    @render.plot
                    def graph_6():
                        graphs = current_graphs()
                        bounds = current_bounds()
                        if len(graphs) >= 6:
                            fig = create_graph(data = df(), actuator = graphs[5], yVar1 = input.y_var(), yVar2 = input.y_var2(), xMin = bounds['minX'], xMax = bounds['maxX'])
                        return fig
                    
        def get_value_box_content(actuator_index):
            """
            Build status value boxes for a specific actuator.

            Retrieves the most recent data point for the selected actuator,
            compares it against predefined thresholds, and returns styled
            UI boxes indicating whether values are within acceptable bounds.

            Args:
                actuator_index (int): Index of actuator on the current page.

            Returns:
                Tag: Shiny UI container with value boxes.
            """
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
            
            # Renders the first actuator status box.
            @render.ui
            def value_box_1():
                return get_value_box_content(0)
            
            # Renders the second actuator status box.
            @render.ui
            def value_box_2():
                return get_value_box_content(1)
            
            # Renders the third actuator status box.
            @render.ui
            def value_box_3():
                return get_value_box_content(2)
            
            # Renders the fourth actuator status box.
            @render.ui
            def value_box_4():
                return get_value_box_content(3)
            
            # Renders the fifth actuator status box.
            @render.ui
            def value_box_5():
                return get_value_box_content(4)
            
            # Renders the sixth actuator status box.
            @render.ui
            def value_box_6():
                return get_value_box_content(5)
    # Tab 2: Metadata        
    with ui.nav_panel("Metadata", value="metadata"):
        ui.h2("Batch and Part Metadata")

        # Returns the part metadata dataframe.
        @reactive.calc
        def part_df():
            return part_metadata_df

        # Returns the batch metadata dataframe.
        @reactive.calc
        def batch_df():
            return batch_metadata_df

        # Summarizes parts by batch for dashboard metrics.
        @reactive.calc
        def batch_summary_df():
            return compute_batch_summary(part_df(), batch_df())

        # Computes the overall metadata summary cards.
        @reactive.calc
        def overall_summary():
            return compute_overall_summary(part_df(), batch_df(), batch_summary_df())
        
        @reactive.calc
        def merged_metadata_df():
            parts = part_df().copy()
            batches = batch_df().copy()

            if parts.empty:
                return pd.DataFrame()

            batch_keep = [c for c in ["BatchID", "PolymerType", "Nanoparticle"] if c in batches.columns]
            if batch_keep:
                parts = parts.merge(batches[batch_keep], on="BatchID", how="left")

            return parts


        @reactive.calc
        def filtered_metadata_df():
            """
            Apply user-selected filters to the metadata dataframe.

            Filters include batch ID, part ID, curing type, part shape,
            and polymer type.

            Returns:
                pd.DataFrame: Filtered metadata dataframe.
            """
            df = merged_metadata_df().copy()

            if df.empty:
                return df

            batch_ids = input.filter_batch_id()
            part_ids = input.filter_part_id()
            curing_types = input.filter_curing_type()
            part_shapes = input.filter_part_shape()
            polymer_types = input.filter_polymer_type()

            if batch_ids and "BatchID" in df.columns:
                df = df[df["BatchID"].astype(str).isin(batch_ids)]

            if part_ids and "PartID" in df.columns:
                df = df[df["PartID"].astype(str).isin(part_ids)]

            if curing_types and "CuringType" in df.columns:
                df = df[df["CuringType"].astype(str).isin(curing_types)]

            if part_shapes and "PartShape" in df.columns:
                df = df[df["PartShape"].astype(str).isin(part_shapes)]

            if polymer_types and "PolymerType" in df.columns:
                df = df[df["PolymerType"].astype(str).isin(polymer_types)]

            return df
        
        @reactive.calc
        def filtered_part_table_df():
            df = filtered_metadata_df().copy()
            return df


        @reactive.calc
        def filtered_batch_table_df():
            batches = batch_df().copy()
            filtered = filtered_metadata_df()

            if batches.empty:
                return batches

            if filtered.empty or "BatchID" not in filtered.columns:
                return batches.iloc[0:0]

            keep_batch_ids = filtered["BatchID"].dropna().astype(str).unique().tolist()

            if "BatchID" in batches.columns:
                return batches[batches["BatchID"].astype(str).isin(keep_batch_ids)]

            return batches
            
        
        
        # Builds a plot-ready metadata dataframe by merging batch info and normalizing numeric fields.
        # Builds the merged metadata table used by the comparison chart.
        @reactive.calc
        def metadata_plot_df():
            parts = part_df().copy()
            batches = batch_df().copy()

            if parts.empty:
                return pd.DataFrame()

            # keep only useful batch-level columns to avoid duplicate clutter
            batch_keep = [c for c in ["BatchID", "PolymerType", "Nanoparticle"] if c in batches.columns]
            if batch_keep:
                parts = parts.merge(batches[batch_keep], on="BatchID", how="left")

            # ensure numeric columns are properly typed for plotting calculations (non-numeric entries will become NaN) 
            numeric_cols = [
                "PartThickness_value",
                "CuringTemperature_value",
                "TestDuration_value",
                "StrainValue_value",
            ]

            for col in numeric_cols:
                if col in parts.columns:
                    parts[col] = pd.to_numeric(parts[col], errors="coerce")

            return parts
        

        # Resets all metadata filter inputs to their default (empty) state.
        @reactive.effect
        @reactive.event(input.reset_metadata_filters)
        def _reset_metadata_filters():
            ui.update_selectize("filter_batch_id", selected=[])
            ui.update_selectize("filter_part_id", selected=[])
            ui.update_selectize("filter_curing_type", selected=[])
            ui.update_selectize("filter_part_shape", selected=[])
            ui.update_selectize("filter_polymer_type", selected=[])

        ui.h4("Summary")

        # Renders the summary metric tiles.
        @render.ui
        def summary_boxes():
            s = overall_summary()

            avg_th = s["avg_thickness_overall"]
            avg_th_txt = f"{avg_th:.2f} mm" if pd.notna(avg_th) else "—"

            tiles = [
                summary_tile("Total Parts", str(s["total_parts"]), bg="#eef2ff"),
                summary_tile("Total Batches", str(s["total_batches"]), bg="#eef2ff"),
                summary_tile("Most Common Polymer", s["most_common_polymer"], bg="#eef2ff"),
                summary_tile("Avg Thickness (overall)", avg_th_txt, bg="#eef2ff"),
            ]

            return ui.div(
                {"style": "display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px;"},
                ui.TagList(*tiles),
            )


        ui.hr()

        ui.h4("Metadata Comparison")

        with ui.layout_columns(col_widths=(5, 7)):
            # LEFT COLUMN: tables stacked
            with ui.div():
                with ui.card():
                    ui.card_header("Part Metadata")

                    @render.data_frame
                    def part_table():
                        return render.DataGrid(filtered_part_table_df())

                ui.br()

                with ui.card():
                    ui.card_header("Batch Metadata")

                    @render.data_frame
                    def batch_table():
                        return render.DataGrid(filtered_batch_table_df())

            # RIGHT COLUMN: chart
            with ui.card():
                ui.card_header("Metadata Comparison Chart")

                @render.plot(height=800)
                def metadata_comparison_plot():
                    """
                    Render a bar chart comparing metadata metrics across groups.

                    Groups data by a selected category (e.g., BatchID, PolymerType)
                    and computes the selected metric (e.g., average thickness).

                    Returns:
                        matplotlib.figure.Figure: Generated bar chart.
                    """
                    df = metadata_plot_df().copy()
                    group_col = input.metadata_group_by()
                    metric_key = input.metadata_y_metric()

                    config = get_metadata_metric_config(metric_key)

                    fig, ax = plt.subplots(figsize=(10, 8))

                    if df.empty or config is None or group_col not in df.columns:
                        ax.text(0.5, 0.5, "No data available", ha="center", va="center", transform=ax.transAxes)
                        return fig

                    source_col = config["source_col"]
                    agg_func = config["agg"]

                    if source_col not in df.columns:
                        ax.text(
                            0.5, 0.5,
                            f"Column '{source_col}' not available",
                            ha="center", va="center", transform=ax.transAxes
                        )
                        return fig

                    plot_base = df.dropna(subset=[group_col])

                    if agg_func == "count":
                        plot_df = (
                            plot_base.groupby(group_col, as_index=False)[source_col]
                            .count()
                            .rename(columns={source_col: "metric_value"})
                            .sort_values("metric_value", ascending=False)
                        )
                    else:
                        plot_df = (
                            plot_base.dropna(subset=[source_col])
                            .groupby(group_col, as_index=False)[source_col]
                            .mean()
                            .rename(columns={source_col: "metric_value"})
                            .sort_values("metric_value", ascending=False)
                        )

                    if plot_df.empty:
                        ax.text(0.5, 0.5, "No plottable data", ha="center", va="center", transform=ax.transAxes)
                        return fig

                    bars = ax.bar(plot_df[group_col].astype(str), plot_df["metric_value"])

                    ax.set_title(f"{config['title']} by {group_col}", fontsize=14, pad=12)
                    ax.set_xlabel(group_col, fontsize=11)
                    ax.set_ylabel(config["label"], fontsize=11)

                    ax.bar_label(
                        bars,
                        fmt="%.2f" if agg_func != "count" else "%d",
                        padding=3,
                        fontsize=10
                    )

                    fig.subplots_adjust(bottom=0.18, top=0.88, left=0.12, right=0.97)
                    return fig



if __name__ == "__main__":
    # Make sure to use debug=False to avoid reloader spawning a new thread
    print("Open the browser")
    app.run(debug=False, port=8000, launch_browser=True)