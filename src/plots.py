import matplotlib
# Set matplotlib backend to be non-interactive to avoid main thread error
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from shiny.express import ui
from faicons import icon_svg


def create_graph(data, actuator, yVar1, yVar2, xMin, xMax):
    """
    Create a dual-axis time series plot for one actuator.

    Filters the input dataframe to the selected actuator, converts DateTime
    values to pandas timestamps, and plots two selected measurement columns
    against time. If no data is available, the function returns a placeholder
    plot instead of failing.

    Args:
        data (pd.DataFrame): Timeseries dataframe containing actuator data.
        actuator (str): Actuator ID to filter and plot.
        yVar1 (str): First measurement column to plot on the left y-axis.
        yVar2 (str): Second measurement column to plot on the right y-axis.
        xMin (datetime | pd.Timestamp | None): Minimum x-axis time bound.
        xMax (datetime | pd.Timestamp | None): Maximum x-axis time bound.

    Returns:
        matplotlib.figure.Figure: Matplotlib figure containing the generated plot.
    """
    df = data[data["actuatorNumber"] == actuator].copy()

    if df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return fig

    part_id = df["partID"].iloc[0] if "partID" in df.columns else "Unknown"
    batch_id = df["batchID"].iloc[0] if "batchID" in df.columns else "Unknown"

    try:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce", utc=True)
        df = df.dropna(subset=["DateTime"]).sort_values("DateTime")

        fig, ax = plt.subplots(figsize=(6, 4))
        ax2 = ax.twinx()

        ax.plot(df["DateTime"], df[yVar1], color="blue")
        ax2.plot(df["DateTime"], df[yVar2], color="orange")

        #ax.set_title(f"Sample {part_id}", fontsize=16)
        ax.set_title(f"Actuator {actuator} | Sample {part_id}", fontsize=16)
        ax.set_xlabel("Time", fontsize=14)
        ax.set_ylabel(yVar1, fontsize=14, color="blue")
        ax2.set_ylabel(yVar2, fontsize=14, color="orange")

        if xMin is not None and xMax is not None:
            ax.set_xlim(pd.to_datetime(xMin), pd.to_datetime(xMax))

        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        plt.tight_layout(pad=1.25)
        return fig

    except Exception as e:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center", transform=ax.transAxes)
        #ax.set_title(f"Sample {part_id}")
        ax.set_title(f"Actuator {actuator} | Sample {part_id}")
        return fig
    

# Helper function to create flagging boxes
def create_flagging_boxes(recentData, flagIntervals, variables, actuatorid):
    """
    Create status value boxes for the most recent actuator readings.

    Compares the latest y1 and y2 values against accepted min/max intervals,
    then builds Shiny value boxes with success or warning icons depending on
    whether each value is inside the accepted range.

    Args:
        recentData (dict): Latest actuator values with keys y1Data and y2Data.
        flagIntervals (dict): Accepted min/max intervals for y1 and y2 values.
        variables (dict): Display names for the selected y-axis variables.
        actuatorid (str): Actuator ID shown in the value box titles.

    Returns:
        list: Shiny value box UI elements for y1 and y2 status.
    """
    # Check whether each latest value is inside its accepted interval.    
    def intervalStatus(data, intervals):
        statuses = {}
        statuses['y1Status'] = intervals['y1Interval']['y1Min'] <= data['y1Data'] <= intervals['y1Interval']['y1Max']
        statuses['y2Status'] = intervals['y2Interval']['y2Min'] <= data['y2Data'] <= intervals['y2Interval']['y2Max']
        return statuses
    
    # Choose success or warning icons based on interval status.
    def get_icons(data, intervals):
        icons = {}
        statuses = intervalStatus(data, intervals)
        icons['y1Icon'] = icon_svg("circle-check").add_class("text-success") if statuses['y1Status'] else icon_svg("triangle-exclamation").add_class("text-danger")
        icons['y2Icon'] = icon_svg("circle-check").add_class("text-success") if statuses['y2Status'] else icon_svg("triangle-exclamation").add_class("text-danger")
        return icons
    
    # Create human-readable status text for each selected variable.
    def get_bottom_text(data, intervals):
        texts = {}
        statuses = intervalStatus(data, intervals)
        texts['y1BotText'] = 'Within Accepted Bounds' if statuses['y1Status'] else 'WARNING: OUTSIDE ACCEPTED BOUNDS'
        texts['y2BotText'] = 'Within Accepted Bounds' if statuses['y2Status'] else 'WARNING: OUTSIDE ACCEPTED BOUNDS'
        return texts
    
    # Choose value box color themes based on interval status.
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


def summary_tile(title: str, value: str, subtitle: str = "", bg: str = "#f5f5f5"):
    """
    Build a styled Shiny UI tile for displaying a summary statistic.

    Used by the metadata tab to show compact dashboard values such as total
    parts, total batches, most common polymer, and average thickness.

    Args:
        title (str): Label shown at the top of the tile.
        value (str): Main value displayed prominently in the tile.
        subtitle (str): Optional smaller text shown below the main value.
        bg (str): Background color for the tile.

    Returns:
        Tag: Shiny UI div containing the formatted summary tile.
    """
    return ui.div(
        {
            "style": (
                f"background:{bg}; border-radius:12px; padding:14px; "
                "min-height:88px; border:1px solid #e6e6e6;"
            )
        },
        ui.tags.div(title, style="font-size:13px; opacity:0.85; margin-bottom:6px;"),
        ui.tags.div(value, style="font-size:26px; font-weight:700; line-height:1.1;"),
        ui.tags.div(subtitle, style="font-size:12px; opacity:0.75; margin-top:6px;") if subtitle else "",
    )