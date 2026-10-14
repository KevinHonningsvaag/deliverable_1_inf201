
# Standard library
import json
from typing import Any

# Third party library
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import numpy as np


ENDPOINT: str = 'https://frost.met.no/observations/v0.jsonld'


def get_client_id() -> str:
    with open("frost_met_id.json", "r", encoding="utf-8") as file:
        credentials = json.load(file)

    return credentials[0]["user_id"]


def request_data(endpoint: str, parameters: dict[str, str], client_id: str) -> list[dict[str, Any]]:
    """Request data from the frost.met.no API. Returns a sentence on how it went"""
    r = requests.get(endpoint, parameters, auth=(client_id,''))
    json_data: dict[str, Any] = r.json()
    if r.status_code == 200:
       data: list[dict[str, Any]] = json_data['data']
       print('Data retrieved from frost.met.no!')
    else:
       print('Error! Returned status code %s' % r.status_code)
       print('Message: %s' % json_data['error']['message'])
       print('Reason: %s' % json_data['error']['reason'])
    data = json_data['data']

    return data


def make_dataframe(data: list[dict[str, Any]], referenceTime: str) -> pd.DataFrame:
    df: pd.DataFrame = pd.json_normalize(data, record_path=['observations'], meta=['sourceId', 'referenceTime'])
    df: pd.DataFrame = df[df["timeOffset"] == referenceTime]
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
    plt.fill_between(dates, temperatures, 0, where=(temperatures >= 0).tolist(), interpolate=True, color="red", zorder=2)
    plt.fill_between(dates, temperatures, 0, where=(temperatures < 0).tolist(), interpolate=True, color="blue", zorder=2)
    plt.title("Mean temperature PT0H 01.01.2025 - 31.12.2025")
    plt.xlabel("Date")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")

def compare_temps(df: pd.DataFrame, df_old: pd.DataFrame) -> None:
    """compare the temps from 1925 and 2025 in the same plot."""
    #To have the old data plotted on the same graph, we need to change the year of the old data to 2025.
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
    #Write the x-axis as months instead with the full date, and set the ticks to be at the start of each month.
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.plot(dates_old, temperatures_old, color="turquoise", label="1925", zorder = 3)
    plt.plot(dates, temperatures, color="black", label="2025", zorder = 2)
    plt.title("Mean temperature PT0H for both 1925 and 2025")
    plt.xlabel("Month")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")
    plt.legend()


def get_mean_temp(client_id: str, referencetime) ->  np.float64:
    parameters: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'mean(air_temperature P1Y)',
        'referencetime': referencetime,
    }
    mean_temp: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    mean_temp_df: pd.DataFrame = make_dataframe(mean_temp, "PT0H")
    mean_temp_value: np.float64 = mean_temp_df['value'].values[0]
    
    return mean_temp_value


def get_median_temp(df: pd.DataFrame) -> float:
    median: float = df['value'].median()

    return median
    


def get_maximum_temp(client_id: str, referencetime:str) -> np.float64:
    parameters: dict[str, str] = {
                'sources': 'SN17850',
                'elements': 'max(air_temperature P1Y)',
                'referencetime': referencetime,
}
    maximum_temp_data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    maximum_temp_df: pd.DataFrame = make_dataframe(maximum_temp_data, 'PT18H')
    maximum_temp: np.float64 = maximum_temp_df['value'].values[0]

    return maximum_temp


def get_minimum_temp(client_id: str, referencetime: str) -> np.float64:
    parameters: dict[str, str] = {
                'sources': 'SN17850',
                'elements': 'min(air_temperature P1Y)',
                'referencetime': referencetime,
}
    minimum_temp_data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    minimum_temp_df: pd.DataFrame = make_dataframe(minimum_temp_data, 'PT18H')
    minimum_temp: np.float64 = minimum_temp_df['value'].values[0]

    return minimum_temp


def summary_temp(mean: np.float64, median: float, minimum: np.float64, maximum: np.float64, year: str) -> None:
    title: str = f"Summary of key values regarding temprature in {year}"
    rows: list[tuple[str,str]] = [
        ("Mean air temprature:", f"{mean}°C"),
        ("Median air temprature:", f"{median:.1f}°C"),
        ("Maximum air temprature:", f"{maximum}°C"),
        ("Mininmum air temprature:", f"{minimum}°C"),
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
    plt.show()


def main() -> None:
    referencetime_2025: str = '2025-01-01/2025-12-31'
    referencetime_1925: str = '1925-01-01/1925-12-31'
    parameters_temp_2025: dict[str, str] = {
    'sources': 'SN17850',
    'elements': 'mean(air_temperature P1D)',
    'referencetime': '2025-01-01/2025-12-31',
    
}
    parameters_temp_1925: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'mean(air_temperature P1D)',
        'referencetime': '1925-01-01/1925-12-31',
    }
    client_id: str = get_client_id()
    
    data_temp_2025: list[dict[str, Any]] = request_data(ENDPOINT, parameters_temp_2025, client_id)
    df_temp_2025: pd.DataFrame = make_dataframe(data_temp_2025, "PT6H")
    plot_temp(df_temp_2025)

    mean_temp_2025_1PY: np.float64 = get_mean_temp(client_id, referencetime_2025)
    median_temp_2025: float = get_median_temp(df_temp_2025)
    maximum_temp_2025: np.float64 = get_maximum_temp(client_id, referencetime_2025)
    minimum_temp_2025: np.float64 = get_minimum_temp(client_id, referencetime_2025)
    summary_temp(mean_temp_2025_1PY, median_temp_2025, minimum_temp_2025, maximum_temp_2025, "2025")

    parameters_precipitation: dict[str, str] = {
        'sources' : 'SN17850',
        'elements' : 'sum(precipitation_amount P1D)',
        'referencetime': '2025-01-01/2025-12-31',
    }
    data_precipitation: list[dict[str, Any]] = request_data(ENDPOINT, parameters_precipitation, client_id)
    df_precipitation: pd.DataFrame = make_dataframe(data_precipitation, "PT6H")
    plot_precipitation_temp(df_precipitation, df_temp_2025)

    
    data_temp_1925: list[dict[str, Any]] = request_data(ENDPOINT, parameters_temp_1925, client_id)
    df_temp_1925: pd.DataFrame = make_dataframe(data_temp_1925, "PT0H")

    mean_temp_1925_1PY: np.float64 = get_mean_temp(client_id, referencetime_1925)
    median_temp_1925: float = get_median_temp(df_temp_1925)
    maximum_temp_1925: float = df_temp_1925['value'].max()
    minimum_temp_1925: float = get_minimum_temp(client_id, referencetime_1925)
    

    summary_temp(
    mean_temp_1925_1PY,
    median_temp_1925,
    minimum_temp_1925,
    maximum_temp_1925,
    "1925"
    )
    plot_temp(df_temp_2025)
    compare_temps(df_temp_2025, df_temp_1925)
    plt.show()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interupted by user")
    finally:
        print("Program completed!")
