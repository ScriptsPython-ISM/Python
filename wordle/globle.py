import requests
import datetime
import re
import subprocess
import json as j
import easygui

url = "https://globle-game.com/assets/index-DYefhQCl.js"
response = requests.get(url)
response.raise_for_status()
js_code = response.text
json = js_code.split("Mn=JSON.parse(`")[1].split("`),W")[0]
countries = j.loads(json)
listLength = len(countries)
url = "https://globle-game.com/assets/Game-D9rMaLVn.js"
response = requests.get(url)
js_code = response.text
password = js_code.split('const it="')[1].split('"')[0]
subprocess.run('"C:/Program Files/nodejs/node.exe" "C:/Users/pmcgi/OneDrive/Desktop/JavaScript/globle/globle.js"')
import decrypt
with open("C:/Users/pmcgi/OneDrive/Desktop/Visual Studio/wordle/globle.txt", "r") as f:
    encoded = f.read()
    f.close()
index = int(decrypt.decrypt(encoded, password))
easygui.textbox("Answer:",text=countries[index]["properties"]["NAME"])