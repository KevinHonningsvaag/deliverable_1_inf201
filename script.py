
# Standard library
import json
from typing import Any

# Third party library
import pandas as pd
import matplotlib.pyplot as plt
import requests
import matplotlib.dates as mdates


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
    data = json_data['data']

    return data

def request_old_data(endpoint: str, old_parameters: dict[str, str], client_id: str) -> list[dict[str, Any]]:
    """Request old data from the frost.met.no API."""
    r = requests.get(endpoint, old_parameters, auth=(client_id,''))
    json_old_data: dict[str, Any] = r.json()
    if r.status_code == 200:
       old_data: list[dict[str, Any]] = json_old_data['data']
       print('Data from 1925 retrieved from frost.met.no!')
    else:
       print('Error! Returned status code %s' % r.status_code)
       print('Message: %s' % json_old_data['error']['message'])
       print('Reason: %s' % json_old_data['error']['reason'])
    old_data = json_old_data['data']

    return old_data


def make_dataframe(data: list[dict[str, Any]]) -> pd.DataFrame:
    """Make a dataframe from the data for 2025."""
    df: pd.DataFrame = pd.json_normalize(data, record_path=['observations'], meta=['sourceId', 'referenceTime'])
    df = df[df["timeOffset"] == "PT0H"]
    df['referenceTime'] = pd.to_datetime(df["referenceTime"])

    return df

def make_dataframe_old(old_data: list[dict[str, Any]]) -> pd.DataFrame:
    """Make a dataframe from the old data from 1925."""
    df_old: pd.DataFrame = pd.json_normalize(old_data, record_path=['observations'], meta=['sourceId', 'referenceTime'])
    df_old = df_old[df_old["timeOffset"] == "PT0H"]
    df_old['referenceTime'] = pd.to_datetime(df_old["referenceTime"])

    return df_old


def plot_temp(df: pd.DataFrame) -> None:
    """Plot the mean temperatures for 2025."""
    dates = df["referenceTime"]
    temperatures = df["value"]
    plt.grid(True, zorder=1, color="black")
    plt.grid(True, which="minor", axis="y", zorder=0, color="gray")
    plt.minorticks_on()
    plt.plot(dates, temperatures, color="black", zorder=1, label="2025")
    plt.fill_between(dates, temperatures, 0, where=(temperatures >= 0).tolist(), interpolate=True, color="red", zorder=2)
    plt.fill_between(dates, temperatures, 0, where=(temperatures < 0).tolist(), interpolate=True, color="blue", zorder=2)
    plt.title("Mean temperature PT0H 01.01.2025 - 31.12.2025")
    plt.xlabel("Date")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")
    plt.legend()

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

def temp_table(mean: float, median: float, min: float, max: float) -> None:
    pass


def main() -> None:
    parameters: dict[str, str] = {
    'sources': 'SN17850',
    'elements': 'mean(air_temperature P1D)',
    'referencetime': '2025-01-01/2025-12-31',
    
}
    old_parameters: dict[str, str] = {
        'sources': 'SN17850',
        'elements': 'mean(air_temperature P1D)',
        'referencetime': '1925-01-01/1925-12-31'
    }
    client_id: str = get_client_id()
    
    data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    old_data: list[dict[str, Any]] = request_old_data(ENDPOINT, old_parameters, client_id)
    df: pd.DataFrame = make_dataframe(data)
    df_old: pd.DataFrame = make_dataframe_old(old_data)
    plot_temp(df)
    compare_temps(df, df_old)
    plt.show()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interupted by user")
    finally:
        print("Program completed!")
