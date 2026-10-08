import pandas as pd

def save_frost_met_id_to_json(user_id: str, client_secret: str) -> None:
   
    """Save the frost_met_id to a JSON file."""
    
    frost_met_id: dict[str, str] = {
        "user_id": user_id,
        "client_secret": client_secret
    }
    df: pd.DataFrame = pd.DataFrame([frost_met_id])
    df.to_json("frost_met_id.json", orient="records", index=False)


# Put in your user ID and client secret here and delete it when the script is done.
user_id: str = "a986c628-3898-4935-9d6c-c9f9b2bf7bf3"
client_secret: str = "007bc2f2-049e-4452-ad50-fe22a27e8ac4"
save_frost_met_id_to_json(user_id, client_secret)