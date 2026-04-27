import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import uri


def readData(
    uri: str,
    server_api: ServerApi,
    dbName: str = "Compression-SPOC-Project",
    collectionName: str = "compression-set-timeseries",
) -> pd.DataFrame:
    """
    Read one timeseries collection and return a dataframe compatible with app.py.
    Uses fixed-schema transforms for the real-time dashboard.
    """
    client = MongoClient(host=uri, server_api=server_api)
    db = client[dbName]

    docs = list(db[collectionName].find())
    if not docs:
        return pd.DataFrame(
            columns=[
                "DateTime",
                "date",
                "time",
                "Time Difference",
                "Position (MachineCount)",
                "Position (mm)",
                "Torque",
                "Force Signal",
                "actuatorID",
                "batchID",
                "partID",
                "actuatorNumber",
            ]
        )

    df = pd.DataFrame(docs)

    # Flatten metadata
    meta = pd.json_normalize(df["metadata"])
    df = pd.concat([df.drop(columns=["metadata", "_id"], errors="ignore"), meta], axis=1)

    # Clean and sort base dataframe FIRST so all columns stay aligned
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce", utc=True)
    df = df.dropna(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)

    # Build app-compatible dataframe
    newdf = pd.DataFrame()

    newdf["DateTime"] = df["DateTime"]
    newdf["date"] = newdf["DateTime"].dt.date
    newdf["time"] = newdf["DateTime"].dt.time
    newdf["Time Difference"] = (
        newdf["DateTime"].diff().dt.total_seconds().fillna(0).cumsum()
    )

    newdf["Position (MachineCount)"] = pd.to_numeric(
        df["PLC_axis1_cyberPtPAxis_PositionActual_Value"], errors="coerce"
    )
    newdf["Position (mm)"] = (newdf["Position (MachineCount)"] / 65536) * 3
    newdf["Torque"] = pd.to_numeric(
        df["PLC_axis1_cyberPtPAxis_TorqueActual_Value"], errors="coerce"
    )
    newdf["Force Signal"] = pd.to_numeric(
        df["PLC_axis1_Axis1_Force_Lb_Value"], errors="coerce"
    )

    newdf["actuatorID"] = df["actuatorID"].astype(str)
    newdf["batchID"] = df["batchID"].astype(str)
    newdf["partID"] = df["partID"].astype(str)
    newdf["actuatorNumber"] = newdf["actuatorID"]

    client.close()
    return newdf


if __name__ == "__main__":
    out = readData(uri=uri, server_api=ServerApi("1"))
    print(f"shape={out.shape}")
    print(f"columns={list(out.columns)}")