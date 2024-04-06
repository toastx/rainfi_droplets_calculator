from flask import Flask,request
import requests

app = Flask(__name__)

RAINFI_PATH = "https://api-v2.rain.fi"

NON_LENDING_DROPLET = 1
LENDING_DROPLET = 2
BORROWING_DROPLET = 3 

@app.route('/droplets', methods=["GET"])
def user_droplets():
    pubkey = request.args.get('pubkey')
    if pubkey == None:
        return "Send proper pubkey"

    token_list = _fetch_price_feed()

    borrow_droplets  = borrow_droplets_count(pubkey=pubkey, token_list= token_list)
    lender_droplets = lender_droplets_count(pubkey=pubkey, token_list= token_list)
    
    droplets = borrow_droplets + lender_droplets

    return {'Daily estimated droplets':droplets, 
            'Borrowing Droplets' : borrow_droplets,  
            'Lending Droplets' :lender_droplets}


def borrow_droplets_count(pubkey, token_list):
    _borrow_droplets = 0
    api_route = "/users/user-stats?owner="
    api_url = RAINFI_PATH + api_route+ pubkey
    headers = {"Content-Type": "application/json"}
    payload = {}
    response = requests.request("GET", api_url, headers=headers , data = payload)
    res = response.json()
    stats = res["rain"]

    for i in stats:
        if i in token_list["prices"]:
            price = token_list["prices"][i]
            decimals = token_list["decimals"][i]
            _curr_volume = stats[i]["currentBorrowedVolume"]
            curr_volume = _curr_volume/10**decimals
            value = curr_volume * price
            _borrow_droplets += float(round(value*BORROWING_DROPLET,1))

    return _borrow_droplets

def lender_droplets_count(pubkey, token_list):
    api_route = "/pools/pool?pubkey="
    pool_pubkey = _fetch_pool_pubkey(pubkey)
    if pool_pubkey == None:
        return 0
    
    api_url = RAINFI_PATH + api_route+ pool_pubkey
    headers = {"Content-Type": "application/json"}
    payload = {}
    response = requests.request("GET", api_url, headers=headers , data = payload)
    res = response.json()
    token_address = res["pool"]["currency"]
    borrowed_amount = int(res["pool"]["borrowedAmount"])
    available_amount = int(res["pool"]["availableAmount"])
    price = token_list["prices"][token_address]
    decimals = token_list["decimals"][token_address]

    lending_droplets = (borrowed_amount/10**decimals) * price * LENDING_DROPLET
    non_lending_droplets = (available_amount/10**decimals) * price * NON_LENDING_DROPLET

    _lender_droplets = float(round(lending_droplets + non_lending_droplets,1))
    return _lender_droplets


def _fetch_price_feed():
    api_route = "/loans/price-feeds"
    api_url = RAINFI_PATH + api_route
    headers = {"Content-Type": "application/json"}
    payload = {}
    response = requests.request("GET", api_url, headers=headers , data = payload)
    res = response.json()
    return res

def _fetch_pool_pubkey(pubkey):
    pool_pubkey = None
    api_route = "/loans/activity-by-user?pubkey="
    api_url = RAINFI_PATH + api_route+ pubkey
    headers = {"Content-Type": "application/json"}
    payload = {}
    response = requests.request("GET", api_url, headers=headers , data = payload)
    res = response.json()
    stats = res["loans"]
    for i in stats:
        if i["lender"] == pubkey:
            pool_pubkey = i["pool"]
    return pool_pubkey if pool_pubkey else None



@app.route('/')
def index():
    return app.send_static_file('droplets.html')

