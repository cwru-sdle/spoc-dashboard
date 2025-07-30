import pandas as pd
import datetime
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import uri

def readData(uri, server_api, dbName):
    """
    Queries data from MongoDB, convert to pandas data frame and process data.

    Args:
        uri (str): MongoDB api key. (Make sure not to type this in, but load it from env)
        server_api (ServerApi): API Version. Typically ServerApi('1).
        dbName (str): Name of database in MongoDB.

    Returns:
        df : Pandas dataframe.
    """

    # Connect to MongoDB 
    client = MongoClient(host = uri, server_api=server_api)
    db = client[dbName]

    df = pd.DataFrame()

    # Names of collections in DB. Here actuators are names of collections
    collection_list = db.list_collection_names()

    # Need to vectorize these loops later.
    for i in range (len(collection_list)):

        col = db[collection_list[i]]
        x = col.find()
        vals = []

        for data in x:
            vals.append(data)
    
        newdf = pd.DataFrame(vals)
        newdf = newdf.drop('_id', axis = 1)
        newdf = newdf.rename(columns={'DateAndTime' : 'dateTime', 
                                      'PLC_axis1_cyberPtPAxis_PositionActual_Value' : 'position(MachineCount)',
                                      'PLC_axis1_cyberPtPAxis_TorqueActual_Value' : 'torque',
                                      'PLC_axis1_Axis1_Force_Lb_Value' : 'forceSignal'})

        newdf['dateTime'] = pd.to_datetime(newdf['dateTime']) # convert string into datetime object in Pandas 
        newdf['date'] = newdf['dateTime'].dt.date # obtain the datetime.date object 
        newdf['time'] = newdf['dateTime'].dt.time # obtain the datetime.time object 
        newdf['timeDifference'] = newdf['dateTime'].diff() # find the difference between each timestamp (row) in the dataset
        newdf['timeDifference'] = newdf['timeDifference'].dt.total_seconds().fillna(0) # Convert difference to seconds only
        newdf['timeDifference'] = newdf['timeDifference'].cumsum() # convert time difference to total time from the beginning of the experiment 
        newdf['position(mm)'] = (newdf['position(MachineCount)']/65536)*3
        newdf['actuatorNumber'] = collection_list[i]
        newdf = newdf.rename(columns={'position(MachineCount)': 'Position (MachineCount)', 
                                      'torque' : 'Torque', 
                                      'forceSignal' : 'Force Signal', 
                                      'timeDifference' : 'Time Difference', 
                                      'position(mm)' : 'Position (mm)'})

        df = pd.concat([df, newdf], ignore_index=True)

    return df

# For testing out function to run separately
if __name__ == "__main__":
    try:
        df = readData(uri, ServerApi('1'), "compression_synthetic")
        print(f"Actuators: {df['actuatorNumber'].unique()}")
        print(f"Dataframe shape: {df.shape}")
        print(f"Columns: {df.columns}")
        print(f"Time Difference: {df['Time Difference'].iloc[-1:].max()}")
        # print(df)
    except Exception as e:
        print(f"Error reading dataframe: {str({e})}") 