import time
import datetime
import requests
import json
import hashlib
import hmac
import math
from datetime import datetime
from urllib.parse import urlencode
BASE_URL = "https://fapi.binance.com"

step_size = {
    'BTCUSDT': 0.00001
}
def round_quantity(quantity, step_size):
    """Rounds the quantity to the nearest step size multiple."""
    return math.floor(quantity / step_size) * step_size
def generate_signature(acc,params):
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    return hmac.new(acc['API_SECRET'].encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_user_wallet_balance(account, quote_asset="USDT"):
    api_key = account['API_KEY']
    api_secret = account['API_SECRET']
    base_url = "https://api.binance.com"
    endpoint = "/sapi/v1/asset/wallet/balance"
    timestamp = int(time.time() * 1000)

    payload = {
        "quoteAsset": quote_asset,
        "timestamp": timestamp
    }

    # Sắp xếp tham số theo thứ tự keys để tạo chữ ký
    query_string = "&".join([f"{key}={payload[key]}" for key in sorted(payload)])
    signature = hmac.new(
        api_secret.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-MBX-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except Exception as e:
            print(f"[PARSE ERROR] {e}")
            return None
    else:
        print(f"[ERROR] Status: {response.status_code}")
        print(f"[ERROR] Body: {response.text}")
        return None

def check_balance(acc):
    try:
        timestamp = int(time.time() * 1000)
        params = {"timestamp": timestamp}
        params["signature"] = generate_signature(acc,params)
        url = f"{BASE_URL}/fapi/v2/account"
        headers = {"X-MBX-APIKEY": acc['API_KEY']}
        response = requests.get(url, headers=headers, params=params).json()
        for asset in response['assets']:
            if asset['asset'] == 'USDT':  # Get USDT futures balance
                print(f"Futures Balance: {asset['availableBalance']}")
                return float(asset['availableBalance'])
        return None
    except Exception as e:
        print(f"Error checking balance: {e}")
        return None


def get_binance_precision(symbol):
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()
    
    for s in data["symbols"]:
        if s["symbol"] == symbol:
            for f in s["filters"]:
                if f["filterType"] == "LOT_SIZE":
                    print(f"Step size for {symbol}: {f['stepSize']}")
                    return float(f["stepSize"])
    return None  # Symbol not found or API error
def new_trade_amount(acc,symbol,amount_usd):
    url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}"
    response = requests.get(url).json()
    price = float(response['price'])
    quantity = amount_usd / price
    step_size = get_binance_precision(symbol)
    round_quantity = round(quantity/ step_size) * step_size
    return round_quantity


def check_open_positions(acc,symbol):
    """ Fetch open futures positions. """
    try:
        timestamp = int(time.time() * 1000)
        params = {"timestamp": timestamp}
        params["signature"] = generate_signature(acc,params)
        url = f"{BASE_URL}/fapi/v2/positionRisk"
        headers = {"X-MBX-APIKEY": acc['API_KEY']}
        response = requests.get(url, headers=headers, params=params).json()
        open_positions = [pos for pos in response if float(pos['positionAmt']) != 0 and pos['symbol'] == symbol]
        if open_positions:
            # print(f"Open Futures Positions: {open_positions}")
            return open_positions
    except Exception as e:
        print(f"Error checking open positions: {e}")
        return None
def check_price(symbol):
    url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}"
    response = requests.get(url).json()
    price = float(response['price'])
    print(f'{symbol} {price}')
    return price

def place_future_order(acc,symbol, side, quantity):
    """ Place futures market order. """
    try:
        timestamp = int(time.time() * 1000)
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
            "timestamp": timestamp
        }
        order_data["signature"] = generate_signature(acc,order_data)
        url = f"{BASE_URL}/fapi/v1/order"
        headers = {"X-MBX-APIKEY": acc['API_KEY']}
        response = requests.post(url, headers=headers, params=order_data).json()

        if "orderId" in response:
            print(f"Order successful: {response}")
        else:
            print(f"Order failed: {response}")
    except Exception as e:
        print(f"Error placing order: {e}")

def check_open_positions(acc,symbol):
    """ Fetch open futures positions. """
    try:
        timestamp = int(time.time() * 1000)
        params = {"timestamp": timestamp}
        params["signature"] = generate_signature(acc,params)
        url = f"{BASE_URL}/fapi/v2/positionRisk"
        headers = {"X-MBX-APIKEY": acc['API_KEY']}
        response = requests.get(url, headers=headers, params=params).json()
        
        open_positions = [pos for pos in response if float(pos['positionAmt']) != 0 and pos['symbol'] == symbol]
        if open_positions:
            print(f"Open Futures Positions: {open_positions}")
        else: print (f'No position for {symbol}')
        return open_positions
    except Exception as e:
        print(f"Error checking open positions: {e}")
        return None

def close_positions(acc,symbol):
    open_positions = check_open_positions(acc,symbol)
    if open_positions:
        print(f"Closing existing positions for {symbol}.")
        for order in open_positions:
            if order['symbol'] == symbol:
                side = "BUY" if float(order['positionAmt']) < 0 else "SELL"
                place_future_order(acc,symbol, side, abs(float(order['positionAmt'])))

def set_leverage(acc,symbol: str, leverage: int):
    params = {
        "symbol": symbol.upper(),  # Ensure symbol is uppercase
        "leverage": leverage,
        "timestamp": int(time.time() * 1000)
    }

    # Generate signature
    params["signature"] = generate_signature(acc, params)

    # Send request
    headers ={"X-MBX-APIKEY": acc['API_KEY']}
    response = requests.post(f"{BASE_URL}/fapi/v1/leverage", params=params, headers=headers)
    print (response.json())

    return response.json() 

def check_leverage(acc: dict, symbol: str):
    
    params = {
        "symbol": symbol.upper(),  # Ensure symbol is uppercase
        "timestamp": int(time.time() * 1000)
    }

    # Generate signature
    params["signature"] = generate_signature(acc, params)

    # Send request
    headers = {"X-MBX-APIKEY": acc.get("API_KEY", "")}
    response = requests.get(f"{BASE_URL}/fapi/v2/positionRisk", params=params, headers=headers)

    data = response.json()

    # Handle API response
    if isinstance(data, list) and len(data) > 0:
        leverage = int(data[0].get("leverage", 0))  # Extract leverage safely
        print (f"symbol: {symbol}, leverage: {leverage}")
        return {"symbol": symbol, "leverage": leverage}
    else:
        return {"error": data}

def check_history(acc,symbol,start_time=None, end_time=None,limit=100):
    url = f"{BASE_URL}/fapi/v1/allOrders"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "timestamp": timestamp,
        "limit": limit
    }
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    query_string = urlencode(params)

    params['signature'] = generate_signature(acc,params)
    headers = {"X-MBX-APIKEY": acc['API_KEY']}
    response = requests.get(f"{url}?{urlencode(params)}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json()}

# Function to send the updated equity to Telegram
def send_message(message,bot_token,chat_id):
    


    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, params=params)
    print(f"📤 Sent to Telegram {response}")  # Check response for errors




# def place_order_quote(acc,symbol, side, quantity): #buy or sell in USDT
#     try:

#         timestamp = int(time.time() * 1000)
#         order_data = {
#             "symbol": symbol,
#             "side": side,
#             "type": "MARKET",
#             "quoteOrderQty": quantity,
#             "timestamp": timestamp
#         }
#         order_data["signature"] = generate_signature(acc,order_data)
#         url = f"{BASE_URL}/api/v3/order"
#         headers = {"X-MBX-APIKEY": acc['API_KEY']}
#         response = requests.post(url, headers=headers, params=order_data).json()
#         print(f"Order placed: {response}")
#     except Exception as e:
#         print(f"Error placing order: {e}")

# def place_order_base(acc,symbol, side, quantity): #buy or sell in btc
#     try:
#         quantity_round = round_quantity(quantity, step_size[symbol])
#         timestamp = int(time.time() * 1000)
#         order_data = {
#             "symbol": symbol,
#             "side": side,
#             "type": "MARKET",
#             "quantity": quantity_round,
#             "timestamp": timestamp
#         }
#         order_data["signature"] = generate_signature(acc,order_data)
#         url = f"{BASE_URL}/api/v3/order"
#         headers = {"X-MBX-APIKEY": acc['API_KEY']}
#         response = requests.post(url, headers=headers, params=order_data).json()
#         print(f"Order placed: {response}")
#     except Exception as e:
#         print(f"Error placing order: {e}")