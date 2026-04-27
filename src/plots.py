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
    Create a time series plot for a given actuator using DateTime as the x-axis.
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


# builds styled tile UI elements for summary stats
def summary_tile(title: str, value: str, subtitle: str = "", bg: str = "#f5f5f5"):
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