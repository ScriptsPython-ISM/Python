import requests

while True:
    request = requests.get("https://data.worldbank.org/indicator/SP.DYN.CDRT.IN?NZ&end=2023&locations=AF-NZ&name_desc=true&start=1960&type=shaded&view=chart")
    print(request.text)
    