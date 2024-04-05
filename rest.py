import requests

def get_price(address):
    price_url = f"https://public-api.birdeye.so/public/price?address={address}"
    headers = {'X-API-KEY': '1d695a0d50ff4603abd7211b9403d15c'}
    response = requests.get(price_url, headers=headers)
    res = response.json()
    return res['data']['value']


api_url = "https://api-v2.rain.fi" + "/users/user-stats?owner=" + "9is85us6rMpZVv63peUFbqq113YnQSNyTT1qGp3DtAru"

headers = {"Content-Type": "application/json"}
payload = {}

response = requests.request("GET", api_url, headers=headers , data = payload)

res = response.json()


droplets = 0

stats = res["rain"]
for i in stats:
    print(i)
    if i == "So11111111111111111111111111111111111111112":
        price = get_price('So11111111111111111111111111111111111111112')
        _curr_volume = stats[i]["currentBorrowedVolume"]
        curr_volume = _curr_volume/1000000000
        usd = curr_volume * price
        droplets += float(round(usd,1))

    elif stats[i]["currentLoans"] != 0:
        _curr_volume = stats[i]["currentBorrowedVolume"]
        curr_volume = _curr_volume//1000000
        droplets += float(round(curr_volume*3,1))


print(droplets)


