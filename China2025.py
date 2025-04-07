import fastf1
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

"""
    2024 Chinese F1 GP 
"""

# Enable FastF1 caching
fastf1.Cache.enable_cache("cache_folder")

# 2024 Race session data.
session_2024 = fastf1.get_session(2024,'Australia','R')
session_2024.load()

# -- Extract lap times --
# We .copy() cause we are modifying the data.
laps_2024 = session_2024.laps[["Driver","LapTime"]].copy()

# -- Clean the data --
# Subset to select where we are looking for NAs
# Inplace = True to modify the current df rather than creating a new one.
laps_2024.dropna(subset=["LapTime"],inplace=True)

# Create a new column to have the time in seconds:
laps_2024["LapTime (s)"] = laps_2024["LapTime"].dt.total_seconds()

# 2025 Qualifying session data:

drivers = """Oscar Piastri
George Russell
Lando Norris
Max Verstappen
Lewis Hamilton
Charles Leclerc
Isack Hadjar
Kimi Antonelli
Yuki Tsunoda
Alex Albon
Esteban Ocon
Nico Hulkenberg
Fernando Alonso
Lance Stroll
Carlos Sainz
Pierre Gasly
Oliver Bearman
Jack Doohan
Gabriel Bortoleto
Liam Lawson"""

drivers = drivers.strip().split('\n')

times = """90,64
90,723
90,793
90,817
90,927
91,021
91,079
91,103
91,638
91,706
91,625
91,632
91,688
91,773
91,840
91,992
92,018
92,092
92,141
92,174
"""
times = times.strip().split('\n')


qualifying_2025 = pd.DataFrame({
    "Driver": drivers,
    "QualifyingTime (s)": times
})

# Create a dictionary with the Driver codes:
driver_mapping = {  "Alexander Albon": "ALB",   "Fernando Alonso": "ALO",       "Kimi Antonelli": "ANT",
                    "Oliver Bearman": "BEA",    "Gabriel Bortoleto": "BOR",     "Valtteri Bottas": "BOT",
                    "Franco Colapinto": "COL",  "Nyck de Vries": "DEV",         "Jack Doohan": "DOO",
                    "Pierre Gasly": "GAS",      "Isack Hadjar": "HAD",          "Lewis Hamilton": "HAM",
                    "Nico Hülkenberg": "HUL",   "Liam Lawson": "LAW",           "Charles Leclerc": "LEC",
                    "Kevin Magnussen": "MAG",   "Lando Norris": "NOR",          "Esteban Ocon": "OCO",
                    "Sergio Pérez": "PER",      "Oscar Piastri": "PIA",         "Daniel Ricciardo": "RIC",
                    "George Russell": "RUS",    "Carlos Sainz": "SAI",          "Logan Sargeant": "SAR",
                    "Lance Stroll": "STR",      "Yuki Tsunoda": "TSU",          "Max Verstappen": "VER",
                    "Zhou Guanyu": "ZHO"

}

# Create a column in the df with the codes so we can merge all the data together:
qualifying_2025["DriverCode"] = qualifying_2025["Driver"].map(driver_mapping)

# Merge the data
# Left_on to tell what column are we joining the data on the left df
# Right_on to tell what column are we joinign the data on the right df.
merged_data = qualifying_2025.merge(laps_2024, left_on="DriverCode", right_on="Driver")


# Use only "QualifyingTime (s)" as a feature for our model. This is because we want to estimate the lap times using the qualifying times:
X = merged_data[["QualifyingTime (s)"]]

y = merged_data[["LapTime (s)"]]

if X.shape[0] == 0:
    raise ValueError("Dataset is empty after preprocessing. Check data sources.")

# -- Train Gradient Boosting Model --
# Data splitting.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# ML model generation.
model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1)

# Model fitting:
model.fit(X_train, y_train)

# Predict using 2025 qualifying times
predicted_lap_times = model.predict(qualifying_2025[["QualifyingTime (s)"]])
qualifying_2025["PredictedRaceTime (s)"] = predicted_lap_times

# Rank drivers by predicted race time
qualifying_2025 = qualifying_2025.sort_values(by="PredictedRaceTime (s)")

# Print final predictions
print("\n🏆 Predicted 2025 Australian GP Winner 🏆\n")
print(qualifying_2025[["Driver", "PredictedRaceTime (s)"]])


# Evaluate Model
y_pred = model.predict(X_test)
print(f"\n📉 Model Error (MAE): {mean_absolute_error(y_test, y_pred):.2f} seconds")