

import json
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import requests
import yaml


ENDPOINT: str = 'https://frost.met.no/observations/v0.jsonld'


def get_client_id() -> str:
    """Gets the client ID from the frost_met_id.json file from the save_user_id.py script."""
    try:
        with open("frost_met_id.json", "r", encoding="utf-8") as file:
            credentials = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError("frost_met_id.json was not found. Run save_user_id.py first.") 
    except OSError:
        raise OSError("Could not read frost_met_id.json.")

    return credentials[0].get("user_id")


def request_data(
        endpoint: str,
        parameters: dict[str, str],
        client_id: str,
) -> list[dict[str, Any]]:
    """Request Frost observations and raise an error if the request fails."""
    try:
        response = requests.get(
            endpoint, params=parameters, auth=(client_id, ''), timeout=30
        )
        response.raise_for_status()
    except requests.Timeout:
        raise requests.Timeout("The request to the Frost API timed out. Try again later.") 
    except requests.RequestException:
        raise requests.RequestException("Could not retrieve data from the Frost API.")

    json_data = response.json()
    data = json_data.get('data')
    if not data:
        raise ValueError("No observations were found for the selected parameters.")

    return data


def make_dataframe(data: list[dict[str, Any]], time_offset: str) -> pd.DataFrame:
    """Create a DataFrame from Frost data and filter by time offset."""
    #   Frost uses nested JSON, so we need to use json_normalize to flatten the data into a dataframe.
    df: pd.DataFrame = pd.json_normalize(
        data,
        record_path=['observations'],
        meta=['sourceId', 'referenceTime']
    )
    df = df[df["timeOffset"] == time_offset]
    df['referenceTime'] = pd.to_datetime(df['referenceTime'])

    return df


def plot_temp(df: pd.DataFrame) -> None:
    """Plot the mean temperatures for 2025."""
    dates = df["referenceTime"]
    temperatures = df["value"]
    plt.grid(True, zorder=1, color="black")
    plt.grid(True, which="minor", axis="y", zorder=0, color="gray")
    plt.minorticks_on()
    plt.plot(dates, temperatures, color="black", zorder=1)
    plt.fill_between(
        dates, 
        temperatures,
        0,
        where=(temperatures >= 0).tolist(),
        interpolate=True,
        color="red",
        zorder=2
    )
    plt.fill_between(
        dates,
        temperatures,
        0,
        where=(temperatures < 0).tolist(),
        interpolate=True,
        color="blue",
        zorder=2
    )
    plt.title("Mean temperature PT0H 01.01.2025 - 31.12.2025")
    plt.xlabel("Date")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")


def compare_temps(df: pd.DataFrame, df_old: pd.DataFrame) -> None:
    """
    Plots the data from 1925 and 2025 in the same plot over the year,
    so that we can visually compare the difference in temperatures.
    """
    # Change the year of the old data to 2025 for comparison purposes
    dates_old = df_old["referenceTime"].apply(
    lambda date: date.replace(year=2025)
    )
    temperatures_old = df_old["value"]
    dates = df["referenceTime"]
    temperatures = df["value"]
    plt.figure(figsize=(10, 5))
    plt.grid(True, zorder=0, color="black")
    plt.grid(True, which="minor", axis="y", zorder=0, color="black")
    plt.minorticks_on()
    # Display month names on the x-axis instead of full dates.
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.plot(dates_old, temperatures_old, color="turquoise", label="1925", zorder=3)
    plt.plot(dates, temperatures, color="black", label="2025", zorder=2)
    plt.title("Mean temperature PT0H for both 1925 and 2025")
    plt.xlabel("Month")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")
    plt.legend()


def get_mean_temp(client_id: str, referencetime: str) -> np.float64:
    """Get the mean temperature for a given year."""
    parameters: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'mean(air_temperature P1Y)',
        'referencetime': referencetime,
    }
    mean_temp: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    # Filters observations using the PT0H time offset.
    mean_temp_df: pd.DataFrame = make_dataframe(mean_temp, "PT0H")
    mean_temp_value: np.float64 = mean_temp_df['value'].values[0]
    
    return mean_temp_value


def get_median_temp(df: pd.DataFrame) -> float:
    """Get the median temperature for a given year."""
    median: float = df['value'].median()

    return median


def get_maximum_temp(client_id: str, referencetime: str) -> np.float64:
    """Get the maximum temperature for a given year."""
    parameters: dict[str, str] = {
                'sources': 'SN17850',
                'elements': 'max(air_temperature P1Y)',
                'referencetime': referencetime,
    }
    maximum_temp_data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    # Filters observations using the PT18H time offset..
    maximum_temp_df: pd.DataFrame = make_dataframe(maximum_temp_data, 'PT18H')
    maximum_temp: np.float64 = maximum_temp_df['value'].values[0]

    return maximum_temp


def get_minimum_temp(client_id: str, referencetime: str) -> np.float64:
    """Get the minimum temperature for a given year."""
    parameters: dict[str, str] = {
                'sources': 'SN17850',
                'elements': 'min(air_temperature P1Y)',
                'referencetime': referencetime,
    }
    minimum_temp_data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    # Filters observations using the PT18H time offset..
    minimum_temp_df: pd.DataFrame = make_dataframe(minimum_temp_data, 'PT18H')
    minimum_temp: np.float64 = minimum_temp_df['value'].values[0]

    return minimum_temp


def summary_temp(
        mean: np.float64, 
        median: float, 
        minimum: np.float64, 
        maximum: np.float64, 
        year: str
) -> None:
    """Print a summary of key values regarding temperature for a given year."""
    title: str = f"Summary of key values regarding temprature in {year}"
    rows: list[tuple[str, str]] = [
        ("Mean air temprature:", f"{mean}°C"),
        ("Median air temprature:", f"{median:.1f}°C"),
        ("Maximum air temprature:", f"{maximum}°C"),
        ("Minimum air temprature:", f"{minimum}°C"),
    ]
    width: int = len(title)
    border: str = f"+{'-' * (width + 2)}+"

    print()
    print(border)
    print(f"| {title} |")
    print(border)
    for label, value in rows:
        print(f"| {label:<{int(width/2)}}{value:>{int(width/2)}} |")
        print(border)
    print()
    if year == '1925':
        print(f"Note that the max temprature and median is calculated from the mean temprature")
    else:
        print(f"Note that the median is calculated from the mean temprature")
    print()


def plot_precipitation_temp(precipitation: pd.DataFrame, temp: pd.DataFrame) -> None:
    """Plot the precipitation and temperature for 2025."""
    dates: pd.Series = precipitation['referenceTime']
    precipitation_values: pd.Series = precipitation['value']
    temp_values: pd.Series = temp['value']
    
    fig, ax1 = plt.subplots()
    ax1.bar(dates, precipitation_values, color="skyblue", zorder=1, label="Precipitation")
    ax1.set_ylabel("Precipitation mm")
    ax1.set_xlabel("Dates")
    ax1.grid(zorder=0)
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(dates, temp_values, color="pink", zorder=1, label="Temprature")
    ax2.set_ylabel("Degrees °C")
    ax2.grid(zorder=0)
    ax2.legend(loc='upper right')
    plt.title("Mean temperature and sum precipitation PTH6  01.01.2025 - 31.12.2025")


def count_heatwaves(df: pd.DataFrame) -> list[str]:
    """
   Find heatwaves using daily maximum temperatures.

    A heatwave is five or more consecutive days with
    maximum temperatures of at least 27°C.

    Return a list containing the start and end dates
    of each heatwave.
    """
    df = df.sort_values("referenceTime")

    heatwaves = []
    consecutive_days = 0
    start_date = None
    previous_date = None

    for _, row in df.iterrows():
        date = row["referenceTime"].date()
        temperature = row["value"]
        if temperature >= 27:
            if consecutive_days == 0:
                start_date = date
                consecutive_days = 1
            elif (date - previous_date).days == 1:
                consecutive_days += 1
            else:
                consecutive_days = 1
                start_date = date
        else:
            if consecutive_days >= 5:
                heatwaves.append(f"{start_date} - {previous_date}")
            consecutive_days = 0

        previous_date = date
    # Checks if the last days of the year form a heatwave
    if consecutive_days >= 5:
        heatwaves.append(f"{start_date} - {previous_date}")

    return heatwaves


def save_heatwaves(
    heatwaves: list[str],
    station_id: str,
    station_name: str,
    year: int
) -> None:
    """Save heatwave information to a YAML file."""
    summary = {
        "dates": heatwaves,
        "station_id": station_id,
        "station_name": station_name,
        "year": year
    }

    # Create a new file or overwrite the existing YAML file.
    with open("heatwave_summary.yml", "w", encoding="utf-8") as file:
        yaml.safe_dump(
            summary,
            file,
            allow_unicode=True,
            sort_keys=False
        )


def analyze_heatwaves(
    client_id: str,
    station_id: str,
    station_name: str,
    year: int
) -> int:
    """Count heatwaves for a station and year, and save a YAML summary."""
    parameters: dict[str, str] = {
        "sources": station_id,
        "elements": "max(air_temperature P1D)",
        "referencetime": f"{year}-01-01/{year + 1}-01-01"
    }
    data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    # Check that PT18H matches the timeOffset returned by Frost
    df: pd.DataFrame = make_dataframe(data, "PT18H")
    heatwaves: list[str] = count_heatwaves(df)
    save_heatwaves(heatwaves, station_id, station_name, year)
    return len(heatwaves)


def get_moving_avrage(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Assign the same mean to each consecutive group of seven daily readings."""
    df: pd.DataFrame = df_temp.sort_values('referenceTime').copy()
    weeks: np.ndarray = np.arange(len(df)) // 7
    df["moving_avrage"] = df.groupby(weeks)["value"].transform("mean")

    return df


def plot_moving_avrage(moving_avrage: pd.DataFrame, mean_temp: pd.DataFrame) -> None:
    plt.figure("Moving 7-day and 1PD mean temprature 2025")
    plt.plot(moving_avrage['referenceTime'], moving_avrage['moving_avrage'], color="Green", zorder=1, label="1PW")
    plt.scatter(mean_temp['referenceTime'], mean_temp['value'], s=2, color="Black", zorder=1, label="1PD")
    plt.xlabel("Date")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black", zorder=0)
    plt.grid(zorder=0)
    plt.title("Moving 7-day and 1PD mean temprature 2025")
    plt.legend()


def main() -> None:
    client_id: str = get_client_id()
    
    referencetime_2025: str = '2025-01-01/2025-12-31'
    parameters_temp_2025: dict[str, str] = {
    'sources': 'SN17850',
    'elements': 'mean(air_temperature P1D)',
    'referencetime': '2025-01-01/2025-12-31',
    }
    data_temp_2025: list[dict[str, Any]] = request_data(ENDPOINT, parameters_temp_2025, client_id)
    df_temp_2025: pd.DataFrame = make_dataframe(data_temp_2025, "PT6H")
    plot_temp(df_temp_2025)

    mean_temp_2025_1py: np.float64 = get_mean_temp(client_id, referencetime_2025)
    median_temp_2025: float = get_median_temp(df_temp_2025)
    maximum_temp_2025: np.float64 = get_maximum_temp(client_id, referencetime_2025)
    minimum_temp_2025: np.float64 = get_minimum_temp(client_id, referencetime_2025)
    summary_temp(
        mean_temp_2025_1py, 
        median_temp_2025, 
        minimum_temp_2025, 
        maximum_temp_2025, 
        "2025"
    )

    parameters_precipitation: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'sum(precipitation_amount P1D)',
        'referencetime': '2025-01-01/2025-12-31',
    }
    data_precipitation: list[dict[str, Any]] = request_data(ENDPOINT, parameters_precipitation, client_id)
    df_precipitation: pd.DataFrame = make_dataframe(data_precipitation, "PT6H")
    plot_precipitation_temp(df_precipitation, df_temp_2025)

    referencetime_1925: str = '1925-01-01/1925-12-31'
    parameters_temp_1925: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'mean(air_temperature P1D)',
        'referencetime': '1925-01-01/1925-12-31',
    }
    data_temp_1925: list[dict[str, Any]] = request_data(
        ENDPOINT,
        parameters_temp_1925,
        client_id
        )
    df_temp_1925: pd.DataFrame = make_dataframe(data_temp_1925, "PT0H")
    mean_temp_1925_1py: np.float64 = get_mean_temp(
        client_id, 
        referencetime_1925
    )
    median_temp_1925: float = get_median_temp(df_temp_1925)
    maximum_temp_1925: float = df_temp_1925['value'].max()
    minimum_temp_1925: np.float64 = get_minimum_temp(client_id, referencetime_1925)
    summary_temp(
    mean_temp_1925_1py,
    median_temp_1925,
    minimum_temp_1925,
    maximum_temp_1925,
    "1925"
    )
    compare_temps(df_temp_2025, df_temp_1925)  

    number_of_heatwaves = analyze_heatwaves(
    client_id,
    "SN17850",
    "Ås",
    2025
    )   
    print(f"Number of heatwaves: {number_of_heatwaves}")

    df_moving_avrage: pd.DataFrame = get_moving_avrage(df_temp_2025)
    plot_moving_avrage(df_moving_avrage, df_temp_2025)
    plt.show()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interupted by user")
    finally:
        print("Program completed!")
