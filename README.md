# SPOC-dashboard: A real-time monitoring and analysis for SPOC aging &amp; compression tests

**Description**

This package is used to run the dashboard for SPOC aging &amp lifetime experiments at Lawerence Livermore National Lab (LLNL). The dashboard quries data from MongoDB every specified interval of time and generate plots to monitor measurements taken during the experiment.

**Features**

* Real-time monitoring of measurements.
* Graphing variable selection.
* Defining X-axis min and max bounds for the graphs.
* Switch between pages to monitor different graphs.
* Status reports to flag if measurements are outside of defined bounds.
* Viewing Metadata 

*More features to be developed in the future*

**Installation**

*Feel free to create a .venv before installing the packages.*

```{bash}
pip install -r requirements.txt
```

**Usage**

A couple things needs to be modified in the scripts to suit the user's use case before launching the dashboard. 

1. Create a `.env` file insice `./src` directory to store your MongoDB API key or edit the path to your API key in `config.py`.

    * **DO NOT** write the api key in `config.py` or any other scripts.

2. Modify the database name to connect to in `app.py` to connect to the appropriate database.

3. The `readData()` function in `query.py` and `plots.py` is written with the assumption that the collection names reflect the actuator number in the experiment. Please feel free to edit the data processing steps to correctly reflect reading in unique actuator numbers.

*Activate .venv before launching the dashboard*

```{bash}
shiny run ./src/app.py
```