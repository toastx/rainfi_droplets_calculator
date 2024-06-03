from flask import Flask,request,render_template, redirect, url_for
import requests

app = Flask(__name__, template_folder='templates')

RAINFI_PATH = "https://api-v2.rain.fi"

NON_LENDING_DROPLET = 1
LENDING_DROPLET = 2
BORROWING_DROPLET = 3

@app.route('/droplets', methods = ['GET'])
def fetch_droplets():
    pubkey = request.args.get('pubkey')
    if pubkey == None:
        return "Send proper pubkey"

    token_list = _fetch_price_feed()

    borrow_droplets  = borrow_droplets_count(pubkey=pubkey, token_list= token_list)
    lender_droplets = lender_droplets_count(pubkey=pubkey, token_list= token_list)

    _active_loans = active_loans(pubkey=pubkey, token_list= token_list)
    
    droplets = borrow_droplets + lender_droplets

    result = {}
    result['droplets'] = droplets
    result['borrow_droplets'] = borrow_droplets
    result[' lender_droplets'] =  lender_droplets
    result[' _active_loans'] =  _active_loans if _active_loans!=None else None
    return render_template('results.html', result=result)


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
    _lender_droplets = 0
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

def active_loans(pubkey,token_list):
    _active_loans = _fetch_active_loans(pubkey)
    lst = []
    for i in _active_loans:
        d = {}
        d["collateral"] = i[0]
        d["collateral_amount"] = i[1]
        collateral_price = token_list["prices"][i[0]]
        d["collateral_value"] = i[1]*collateral_price
        d["borrowed"] = i[2]
        _borrow_amount = int(i[3])
        _borrow_decimals = token_list["decimals"][i[2]]
        d["borrowed_amount"] = _borrow_amount/10**_borrow_decimals
        borrow_price = token_list["prices"][i[2]]
        d["borrowed_value"] = d["borrowed_amount"] *borrow_price
        d["daily_droplets"] = d["borrowed_value"]*BORROWING_DROPLET
        lst.append(d)
    
    return lst if len(lst)>0 else None



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

def _fetch_active_loans(pubkey):
    api_route = "/loans/user?pubkey="
    api_params = "&platform=Rain&status=Ongoing"
    url = RAINFI_PATH + api_route + pubkey + api_params
    headers = {"Content-Type": "application/json"}
    payload = {}
    response = requests.request("GET", url , headers = headers, data = payload)
    res = response.json()
    _active_loans = res["loans"]
    loan_lst = []
    for i in _active_loans:

        collateral = i["mint"]
        collateral_amount = i["collateralAmount"]
        collateral_decimals = i["collateralDecimals"]
        collateral_value = float(round(int(collateral_amount)/10**collateral_decimals,2))
        borrowed = i["currency"]
        borrowed_amount = i["amount"]
        loan_id = i["pubkey"]
        created_time = i["createdAt"]
        expiry_time = i["expiredAt"]

        _loan_list = [collateral,collateral_value,borrowed,borrowed_amount,created_time,expiry_time,loan_id]
        loan_lst.append(_loan_list)

    return loan_lst


@app.route("/")
def index():
    return render_template("droplets.html")
