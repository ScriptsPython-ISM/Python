import requests

while True:
    request = requests.get("https://www.craiyon.com/en")
    print(request.text)
    