# import useful Python libraries
import matplotlib
# Set matplotlib backend to be non-interactive to avoid main thread error
matplotlib.use('Agg') 

import matplotlib.pyplot as plt
import re

def create_graph(data, actuator, xVar, yVar1, yVar2, xMin, xMax):
    """
    Create a time series plot for a given actuator.

    Args:
        data (pd.DataFrame): Data for making the plots.
        actuator (str): Actuator  to plot.
        xVar: User input for x-axis variable.
        yVar1: User input for y-axis 1 variable.
        yVar2: User input for y-axis 2 variable.
        xMin: Lower bound of the x-axis.
        xMax: Upper bound of the x-axis.

    Returns:
        fig: Matplotlib figure.

    """

    df = data[data['actuatorNumber'] == actuator]
    # get the number of the actuator number
    actuator_num = re.search(r"(?<=tor)[0-9]+",actuator).group()
    try:
        # clear existing plots to avoid caches
        plt.clf()

        fig, ax = plt.subplots(figsize=(6, 4))
        ax2 = ax.twinx()

        ax.plot(df[xVar], df[yVar1], color = "blue")
        ax2.plot(df[xVar], df[yVar2], color = "orange")
        
        ax.set_title(f"Sample {actuator_num}. Actuator {actuator_num}.", fontsize = 16)
        ax.set_xlabel(xVar, fontsize = 14)
        ax.set_ylabel(yVar1,fontsize = 14, color = "blue")
        ax2.set_ylabel(yVar2,fontsize = 14, color = "orange")
        ax.set_xlim(xMin, xMax)

        plt.tight_layout(pad=1.25)
        plt.xlim(xMin, xMax)
        
        return fig
    
    except Exception as e:
        plt.clf()
        # Return empty figure with error message
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, f"Error: {str(e)}", 
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f"Sample {actuator_num}. Actuator {actuator_num}.")
        return fig
        