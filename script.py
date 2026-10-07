
# Standard library
import json
from typing import Any

# Third party library
import pandas as pd
import matplotlib.pyplot as plt
import requests


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


def make_dataframe(data: list[dict[str, Any]]) -> pd.DataFrame:
    df: pd.DataFrame = pd.json_normalize(data, record_path=['observations'], meta=['sourceId', 'referenceTime'])
    df: pd.DataFrame = df[df["timeOffset"] == "PT0H"]
    df['referenceTime'] = pd.to_datetime(df["referenceTime"])

    return df


def plot_temp(df: pd.DataFrame) -> None:
    dates = df["referenceTime"]
    temperatures = df["value"]
    plt.plot(dates, temperatures, color="black")
    plt.fill_between(dates, temperatures, 0, where=temperatures >= 0, interpolate=True, color="red")
    plt.fill_between(dates, temperatures, 0, where=temperatures < 0, interpolate=True, color="blue")
    plt.title("Mean temperature PT0H 01.01.2025 - 31.12.2025")
    plt.xlabel("Date")
    plt.ylabel("Degrees °C")
    plt.axhline(y=0, linestyle="--", color="black")
    plt.show()


def temp_table(mean: float, median: float, min: float, max: float) -> None:
    pass


def main() -> None:
    parameters: dict[str, str] = {
    'sources': 'SN17850',
    'elements': 'mean(air_temperature P1D)',
    'referencetime': '2025-01-01/2025-12-31',
}
    client_id: str = get_client_id()
    
    data: list[dict[str, Any]] = request_data(ENDPOINT, parameters, client_id)
    df: pd.DataFrame = make_dataframe(data)
    plot_temp(df)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interupted by user")
    finally:
        print("Program completed!")
