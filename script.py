
import requests
import json


import pandas as pd
import matplotlib.pyplot as plt


sources: str = "SN17850"
elements: str = 'mean(air_temperature P1D)'
referencetime: str = '2025-01-01/2025-12-31'
timeOffset: str = 'PT6H'
endpoint: str = 'https://frost.met.no/observations/v0.jsonld'
parameters: dict[str, str] = {
    'sources': sources,
    'elements': elements,
    'referencetime': referencetime,
}


def get_client_id() -> str:
    with open("frost_met_id.json", "r", encoding="utf-8") as file:
        credentials = json.load(file)

    return credentials[0]["user_id"]


def request_data(endpoint: str, parameters: dict[str, str], client_id) -> dict[str, float]:
    r = requests.get(endpoint, parameters, auth=(client_id,''))
    json = r.json()
    if r.status_code == 200:
       data = json['data']
       print('Data retrieved from frost.met.no!')
    else:
       print('Error! Returned status code %s' % r.status_code)
       print('Message: %s' % json['error']['message'])
       print('Reason: %s' % json['error']['reason'])
    data: dict[str, float] = json['data']

    return data


def make_dataframe(data: dict[str, float]) -> pd.DataFrame:
    df: pd.DataFrame = pd.json_normalize(data, record_path=['observations'], meta=['sourceId', 'referenceTime'])
    df: pd.DataFrame = df[df["timeOffset"] == "PT0H"]
    #df: pd.DataFrame = df.set_index('referenceTime')
    df['referenceTime'] = pd.to_datetime(df["referenceTime"])

    return df


def plot_temp(df: pd.DataFrame) -> None:
    positive = df['value'].where(df['value']>=0)
    negative = df['value'].where(df['value']<=0)
    plt.plot(df['referenceTime'], df['value'], color="green", label="Rapid changes betwen ±")
    plt.plot(df['referenceTime'], positive, color="red", label="Above 0C°")
    plt.plot(df['referenceTime'], negative, color= "blue", label="Bellow 0C°")
    plt.title("Mean temprature PT0H 01.01.2025 - 31.12.2025")
    plt.xlabel("Date")
    plt.ylabel("Degres C°")
    plt.axhline(y=0, linestyle="--", color="black")
    plt.legend()
    plt.show()
    #plt.savefig("plot_temp")


def temp_table(mean, median, min, max):
    pass


def main() -> None:
    client_id: str = get_client_id()
    data: dict[str, float] = request_data(endpoint, parameters, client_id)
    df: pd.DataFrame = make_dataframe(data)
    plot_temp(df)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interupted by user")
    finally:
        print("Program completed!")
