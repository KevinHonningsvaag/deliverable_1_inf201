
# Standard library
import json
from statistics import median_grouped
from typing import Any

# Third party library
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np


ENDPOINT: str = 'https://frost.met.no/observations/v0.jsonld'


def get_client_id() -> str:
    with open("frost_met_id.json", "r", encoding="utf-8") as file:
        credentials = json.load(file)

    return credentials[0]["user_id"]


def request_data(endpoint: str, parameters: dict[str, str], client_id: str) -> list[dict[str, Any]]:
    r = requests.get(endpoint, parameters, auth=(client_id,''))
    json_data: dict[str, Any] = r.json()
    if r.status_code == 200:
       data: list[dict[str, Any]] = json_data['data']
       print('Data retrieved from frost.met.no!')
    else:
       print('Error! Returned status code %s' % r.status_code)
       print('Message: %s' % json_data['error']['message'])
       print('Reason: %s' % json_data['error']['reason'])
    data: list[dict[str, Any]] = json_data['data']

    return data


def make_dataframe(data: list[dict[str, Any]], referenceTime: str) -> pd.DataFrame:
    df: pd.DataFrame = pd.json_normalize(data, record_path=['observations'], meta=['sourceId', 'referenceTime'])
    df: pd.DataFrame = df[df["timeOffset"] == referenceTime]
    df['referenceTime'] = pd.to_datetime(df['referenceTime'])

    return df


def plot_temp(df: pd.DataFrame) -> None:
    dates = df["referenceTime"]
    temperatures = df["value"]
    plt.plot(dates, temperatures, color="black")
    plt.fill_between(dates, temperatures, 0, where=temperatures >= 0, interpolate=True, color="red")
    plt.fill_between(dates, temperatures, 0, where=temperatures < 0, interpolate=True, color="blue")
    plt.title("Mean temperature PT6H 01.01.2025 - 31.12.2025")
    plt.xlabel("Date")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")
    plt.show()


def get_mean_temp(client_id: str) ->  np.float64:
    parameters: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'mean(air_temperature P1Y)',
        'referencetime': '2025-01-01/2025-12-31',
    }
    mean_temp: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    mean_temp_df: pd.DataFrame = make_dataframe(mean_temp, "PT0H")
    mean_temp_value: np.float64 = mean_temp_df['value'].values[0]
    
    return mean_temp_value


def get_median_temp(df: pd.DataFrame) -> float:
    array = df['value'].values
    median: float = median_grouped(array)

    return median
    


def get_maximum_temp(client_id: str) -> np.float64:
    parameters: dict[str, str] = {
                'sources': 'SN17850',
                'elements': 'max(air_temperature P1Y)',
                'referencetime': '2025-01-01/2025-12-31',
}
    maximum_temp_data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    maximum_temp_df: pd.DataFrame = make_dataframe(maximum_temp_data, "PT18H")
    maximum_temp: np.float64 = maximum_temp_df['value'].values[0]

    return maximum_temp


def get_minimum_temp(client_id: str) -> np.float64:
    parameters: dict[str, str] = {
                'sources': 'SN17850',
                'elements': 'min(air_temperature P1Y)',
                'referencetime': '2025-01-01/2025-12-31',
}
    minimum_temp_data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    minimum_temp_df: pd.DataFrame = make_dataframe(minimum_temp_data, "PT18H")
    minimum_temp: np.float64 = minimum_temp_df['value'].values[0]

    return minimum_temp


def summary_temp_2025(mean: np.float64, median: float, minimum: np.float64, maximum: np.float64) -> None:
    title = f"Summary of key values regarding temprature in 2025"
    rows = [
        ("Mean air temprature:", f"{mean}°C"),
        ("Median air temprature:", f"{median}°C"),
        ("Maximum air temprature:", f"{maximum}°C"),
        ("Mininmum air temprature:", f"{minimum}°C"),
    ]
    width = len(title)
    border = f"+{'-' * (width + 2)}+"

    print()
    print(border)
    print(f"| {title:<{width}} |")
    print(border)
    for label, value in rows:
        print(f"| {label:<{int(width/2)}} {value:>{int(width/2-1)}} |")
        print(border)
    print()


def main() -> None:
    parameters_temp_2025: dict[str, str] = {
    'sources': 'SN17850',
    'elements': 'mean(air_temperature P1D)',
    'referencetime': '2025-01-01/2025-12-31',
}
    client_id: str = get_client_id()
    
    data_temp_2025: list[dict[str, Any]] = request_data(ENDPOINT, parameters_temp_2025, client_id)
    df_temp_2025: pd.DataFrame = make_dataframe(data_temp_2025, "PT6H")
    plot_temp(df_temp_2025)

    parameters_precipitation: dict[str, str] = {
        'sources' : 'SN17850',
        'elements' : 'sum(precipitation_amount P1D)',
        'referencetime': '2025-01-01/2025-12-31',
    }
    data_precipitation: list[dict[str, Any]] = request_data(ENDPOINT, parameters_precipitation, client_id)
    df_precipitation: pd.DataFrame = make_dataframe(data_precipitation, "PT6H")

    mean_temp_2025_1PY = get_mean_temp(client_id)
    median_temp_2025 = get_median_temp(df_temp_2025)
    maximum = get_maximum_temp(client_id)
    minimum = get_minimum_temp(client_id)
    summary_temp_2025(mean_temp_2025_1PY, median_temp_2025, minimum, maximum)    


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interupted by user")
    finally:
        print("Program completed!")
