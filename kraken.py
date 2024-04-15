import requests
import json
import hashlib
import hmac
from base64 import b64encode, b64decode
from urllib.parse import urlencode
import time

class KrakenAPI:

    def __init__(self, api_key:str, api_secret:str):
        self.api_key = api_key
        self.api_secret = api_secret

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
    
    def get_signature(self, url, data):

        postdata = urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = url.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(b64decode(self.api_secret), message, hashlib.sha512)
        sigdigest = b64encode(mac.digest())
        return sigdigest.decode()
    
    @staticmethod
    def handle_response(response:requests.Response):
        if response.ok:
            try:
                json = response.json()
            except requests.exceptions.JSONDecodeError:
                raise KrakenAPI.APIError("Response was not JSON")
            if (error:=json["error"]):
                raise KrakenAPI.APIError(f"API request failed. The following error was returned: {error}")
            return json
        else:
            raise KrakenAPI.APIError("Unable to contact API")

    @staticmethod
    def get_request(url:str, **kwargs):
        response = requests.get(url, **kwargs)
        return KrakenAPI.handle_response(response)
        
    def post_request(self, url:str, data:dict, **kwargs):
        data = data | {"nonce": str(int(time.time()*1000))}
        response = requests.post(
            url,
            headers={
                "API-Key": self.api_key,
                "API-Sign": self.get_signature(url, data),
            },
            data=data,
            **kwargs
        )
        return KrakenAPI.handle_response(response)
    
    @staticmethod
    def get_spot_price(pair:str):
        """
        Gets the current spot price of the specified pair.
        :param pair: A currency pair e.g. "xbtusd"
        """

        curr_a = pair[:3]
        curr_b = pair[3:]

        json = KrakenAPI.get_request(KrakenAPI.endpoint_url("Ticker"), params={"pair": pair})
        try:
            return float(json["result"][f"X{curr_a.upper()}Z{curr_b.upper()}"]["a"][0])
        except:
            raise KrakenAPI.APIError(f"Unexpected response format: {json}")
        
    def place_order(self, pair:str, volume:float, validate:bool=False):
        """
        Places a market buy order against the specified pair.
        :param pair: A currency pair e.g. "xbtusd"
        :param volume: The amount to buy.
        :param validate: If True, the order will not be placed (this can be used for test purposes).
        """

        return self.post_request(KrakenAPI.endpoint_url("AddOrder"),
            {
                "pair": pair,
                "volume": volume,
                "type": "buy",
                "ordertype": "market",
                "validate": validate,
            }
        )


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

try:
    btc_spot = KrakenAPI.get_spot_price(config["pair"])
except KrakenAPI.APIError as e:
    raise SystemExit(f"Unable to get spot price. {e}")
order_value_btc = config["spend"] / btc_spot
print(f'Current BTC price: £{btc_spot}')
print(f'Order Value: £{config["spend"]} -> \u20bf{order_value_btc:.8f}')

api_instance = KrakenAPI(config["api_key"], config["api_secret"])
order_json = api_instance.place_order(config["pair"], order_value_btc, True)
