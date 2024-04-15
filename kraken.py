import requests
import json

class KrakenAPI:

    class APIError (Exception):
        "An error occurred when attempting to call the API"

    endpoints = {"public": ["Ticker"], "private": ["AddOrder"]}

    @staticmethod
    def endpoint_type(endpoint:str):
        for key in KrakenAPI.endpoints:
            if endpoint in KrakenAPI.endpoints[key]:
                return key
        raise ValueError("Invalid endpoint")

    @staticmethod
    def endpoint_url(endpoint:str):
        return f"https://api.kraken.com/0/{KrakenAPI.endpoint_type(endpoint)}/{endpoint}"
    
    @staticmethod
    def get_spot_price(pair:str):

        curr_a = pair[:3]
        curr_b = pair[3:]

        response = requests.get(KrakenAPI.endpoint_url("Ticker"), params={"pair": pair})
        if response.ok:
            try:
                json = response.json()
            except requests.exceptions.JSONDecodeError:
                raise KrakenAPI.APIError("Response was not JSON")
            try:
                return float(json["result"][f"X{curr_a.upper()}Z{curr_b.upper()}"]["a"][0])
            except:
                raise KrakenAPI.APIError(f"Unexpected response format: {json}")
        else:
            raise KrakenAPI.APIError("Unable to contact API")
        
try:
    config_file = open("config.json")
except:
    raise SystemExit("No config.json file found in this directory")
try:
    config = json.load(config_file)
except:
    raise SystemExit("config.json is not valid JSON")
for key in ["api_key", "api_secret", "pair", "spend"]:
    if key not in config:
        raise SystemExit(f"Missing required key '{key}' in config.json.")

btc_spot = KrakenAPI.get_spot_price(config["pair"])
order_value_btc = config["spend"] / btc_spot
print(f'Current BTC price: £{btc_spot}')
print(f'Order Value: £{config["spend"]} -> \u20bf{order_value_btc:.8f}')
