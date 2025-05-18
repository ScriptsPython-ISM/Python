from selenium import webdriver
import json as j
from datetime import datetime
import time
import re
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import easygui

options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=./User_Data") 
options.add_argument("--profile-directory=Default")  
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-background-networking")
options.add_argument("--disable-default-apps")
options.add_argument("--disable-sync")
options.add_argument("--disable-extensions")
options.add_argument("--disable-notifications")
options.add_argument("--mute-audio")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-popup-blocking")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--remote-debugging-port=9222")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_path = "C:/Users/pmcgi/Downloads/chrome-win64/chrome-win64/chrome.exe"
options.binary_location = chrome_path

service = Service("C:/Users/pmcgi/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")

def wordle(yyyy,MM,DD):
    if len(DD) == 1:
        DD = '0'+DD
    if len(mm) == 1:
        MM = '0'+MM
    json = requests.get(f"https://www.nytimes.com/svc/wordle/v2/{yyyy}-{MM}-{DD}.json").text
    reader = j.loads(json)
    easygui.textbox("Answer:", text=reader['solution'])
def connections(yyyy,MM,DD):
    if len(DD) == 1:
        DD = '0'+DD
    if len(mm) == 1:
        MM = '0'+MM
    json = requests.get(f"https://www.nytimes.com/svc/connections/v1/{yyyy}-{MM}-{DD}.json").text
    reader = j.loads(json)
    for i in range(4):
        try:
            easygui.textbox(text=str(dict(reader["groups"])[list(reader["groups"])[int(easygui.integerbox("Level:"))]]["members"]))
        except TypeError:
            break
def hardle(yyyy,mm,dd):
    driver.get("https://hardle.org")
    time.sleep(2)
    target_url = driver.find_element(By.XPATH, "//link[contains(@href, '/_app/immutable/chunks/TrashIcon') and contains(@href, '.js')]").get_attribute("href")
    driver.quit()
    
    if target_url:
        response = requests.get(target_url)
        content = response.text
        content = content.split("Map(")[1].split("),ms")[0]
        content = dict(eval(content))
        easygui.textbox("Answer:", text=content[f"{dd}.{mm}.{yyyy}"])
    else:
        print("Couldn't find the TrashIcon JS file.")
def worldle():
    driver.get("https://worldle.teuteuf.fr/")
    answer = driver.find_element(By.XPATH, "//img[contains(@src, '/country-shapes/') and @alt='country to guess']").get_attribute("src")
    answer = answer.removeprefix("https://dashboard-assets.teuteuf.fr/data/common/country-shapes/").removesuffix(".svg")
    countries = {"AF":"Afghanistan","AX":"Aland Islands","AL":"Albania","DZ":"Algeria","AS":"American Samoa","AD":"Andorra","AO":"Angola","AI":"Anguilla","AQ":"Antarctica","AG":"Antigua and Barbuda","AR":"Argentina","AM":"Armenia","AW":"Aruba","AU":"Australia","AT":"Austria","AZ":"Azerbaijan","BS":"Bahamas","BH":"Bahrain","BD":"Bangladesh","BB":"Barbados","BY":"Belarus","BE":"Belgium","BZ":"Belize","BJ":"Benin","BM":"Bermuda","BT":"Bhutan","BO":"Bolivia, Plurinational State of","BQ":"Bonaire, Sint Eustatius and Saba","BA":"Bosnia and Herzegovina","BW":"Botswana","BV":"Bouvet Island","BR":"Brazil","IO":"British Indian Ocean Territory","BN":"Brunei Darussalam","BG":"Bulgaria","BF":"Burkina Faso","BI":"Burundi","KH":"Cambodia","CM":"Cameroon","CA":"Canada","CV":"Cape Verde","KY":"Cayman Islands","CF":"Central African Republic","TD":"Chad","CL":"Chile","CN":"China","CX":"Christmas Island","CC":"Cocos (Keeling) Islands","CO":"Colombia","KM":"Comoros","CG":"Congo","CD":"Congo, The Democratic Republic of the","CK":"Cook Islands","CR":"Costa Rica","CI":"Côte d'Ivoire","HR":"Croatia","CU":"Cuba","CW":"Curaçao","CY":"Cyprus","CZ":"Czech Republic","DK":"Denmark","DJ":"Djibouti","DM":"Dominica","DO":"Dominican Republic","EC":"Ecuador","EG":"Egypt","SV":"El Salvador","GQ":"Equatorial Guinea","ER":"Eritrea","EE":"Estonia","ET":"Ethiopia","FK":"Falkland Islands (Malvinas)","FO":"Faroe Islands","FJ":"Fiji","FI":"Finland","FR":"France","GF":"French Guiana","PF":"French Polynesia","TF":"French Southern Territories","GA":"Gabon","GM":"Gambia","GE":"Georgia","DE":"Germany","GH":"Ghana","GI":"Gibraltar","GR":"Greece","GL":"Greenland","GD":"Grenada","GP":"Guadeloupe","GU":"Guam","GT":"Guatemala","GG":"Guernsey","GN":"Guinea","GW":"Guinea-Bissau","GY":"Guyana","HT":"Haiti","HM":"Heard Island and McDonald Islands","VA":"Holy See (Vatican City State)","HN":"Honduras","HK":"Hong Kong","HU":"Hungary","IS":"Iceland","IN":"India","ID":"Indonesia","IR":"Iran, Islamic Republic of","IQ":"Iraq","IE":"Ireland","IM":"Isle of Man","IL":"Israel","IT":"Italy","JM":"Jamaica","JP":"Japan","JE":"Jersey","JO":"Jordan","KZ":"Kazakhstan","KE":"Kenya","KI":"Kiribati","KP":"Korea, Democratic People's Republic of","KR":"Korea, Republic of","KW":"Kuwait","KG":"Kyrgyzstan","LA":"Lao People's Democratic Republic","LV":"Latvia","LB":"Lebanon","LS":"Lesotho","LR":"Liberia","LY":"Libya","LI":"Liechtenstein","LT":"Lithuania","LU":"Luxembourg","MO":"Macao","MK":"Macedonia, Republic of","MG":"Madagascar","MW":"Malawi","MY":"Malaysia","MV":"Maldives","ML":"Mali","MT":"Malta","MH":"Marshall Islands","MQ":"Martinique","MR":"Mauritania","MU":"Mauritius","YT":"Mayotte","MX":"Mexico","FM":"Micronesia, Federated States of","MD":"Moldova, Republic of","MC":"Monaco","MN":"Mongolia","ME":"Montenegro","MS":"Montserrat","MA":"Morocco","MZ":"Mozambique","MM":"Myanmar","NA":"Namibia","NR":"Nauru","NP":"Nepal","NL":"Netherlands","NC":"New Caledonia","NZ":"New Zealand","NI":"Nicaragua","NE":"Niger","NG":"Nigeria","NU":"Niue","NF":"Norfolk Island","MP":"Northern Mariana Islands","NO":"Norway","OM":"Oman","PK":"Pakistan","PW":"Palau","PS":"Palestinian Territory, Occupied","PA":"Panama","PG":"Papua New Guinea","PY":"Paraguay","PE":"Peru","PH":"Philippines","PN":"Pitcairn","PL":"Poland","PT":"Portugal","PR":"Puerto Rico","QA":"Qatar","RE":"Réunion","RO":"Romania","RU":"Russian Federation","RW":"Rwanda","BL":"Saint Barthélemy","SH":"Saint Helena, Ascension and Tristan da Cunha","KN":"Saint Kitts and Nevis","LC":"Saint Lucia","MF":"Saint Martin (French part)","PM":"Saint Pierre and Miquelon","VC":"Saint Vincent and the Grenadines","WS":"Samoa","SM":"San Marino","ST":"Sao Tome and Principe","SA":"Saudi Arabia","SN":"Senegal","RS":"Serbia","SC":"Seychelles","SL":"Sierra Leone","SG":"Singapore","SX":"Sint Maarten (Dutch part)","SK":"Slovakia","SI":"Slovenia","SB":"Solomon Islands","SO":"Somalia","ZA":"South Africa","GS":"South Georgia and the South Sandwich Islands","ES":"Spain","LK":"Sri Lanka","SD":"Sudan","SR":"Suriname","SS":"South Sudan","SJ":"Svalbard and Jan Mayen","SZ":"Swaziland","SE":"Sweden","CH":"Switzerland","SY":"Syrian Arab Republic","TW":"Taiwan, Province of China","TJ":"Tajikistan","TZ":"Tanzania, United Republic of","TH":"Thailand","TL":"Timor-Leste","TG":"Togo","TK":"Tokelau","TO":"Tonga","TT":"Trinidad and Tobago","TN":"Tunisia","TR":"Turkey","TM":"Turkmenistan","TC":"Turks and Caicos Islands","TV":"Tuvalu","UG":"Uganda","UA":"Ukraine","AE":"United Arab Emirates","GB":"United Kingdom","US":"United States","UM":"United States Minor Outlying Islands","UY":"Uruguay","UZ":"Uzbekistan","VU":"Vanuatu","VE":"Venezuela, Bolivarian Republic of","VN":"Viet Nam","VG":"Virgin Islands, British","VI":"Virgin Islands, U.S.","WF":"Wallis and Futuna","EH":"Western Sahara","YE":"Yemen","ZM":"Zambia","ZW":"Zimbabwe"}
    easygui.textbox("Answer:", text=countries[answer.upper()])
def globle():
    import globle

while True:
    yyyy = datetime.now().year
    mm = str(datetime.now().month)
    dd = str(datetime.now().day)

    try:
        target = easygui.choicebox("Target Site:", choices=["Wordle", "Hardle", "Worldle", "Globle", "Connections"]).lower()
    except AttributeError:
        break

    if target == "wordle":wordle(yyyy,mm,dd)
    elif target == "hardle":
        driver = webdriver.Chrome(service=service, options=options)
        hardle(yyyy,mm,dd)
    elif target == "worldle":
        driver = webdriver.Chrome(service=service, options=options)
        worldle()
    elif target == "globle":
        globle()
    elif target == "connections":connections(yyyy,mm,dd)