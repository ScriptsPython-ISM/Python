from pyautogui import *
import time
import numpy as np
import re

FAILSAFE = True

while True:
    click(x=1445, y=1161, clicks=1, button="left")
    click(x=700, y=100, clicks=1, button="left")
    x,y,width,height = locateOnScreen("image.png")
    click(x=x+width/2, y=y+height/2, clicks=1, button='left')
    for i in range(20):
        hotkey("shift", "up")
    hotkey("ctrl", "c")
    click(x=700, y=100, clicks=1, button="left")
    click(x=1300, y=1200)
    click(y=1074)
    hotkey("ctrl", "v")
    hotkey("enter")
    name = input()
    if re.search(r'N....r|n....r|n...a|N...a|d.h|D.h|banana|Banana|ez|Ez|EZ|b.......y|B.......y', name):
        click(x=1445, y=1161, clicks=1, button="left")
        click(x=700, y=100, clicks=1, button="left")
        try:
            x,y,width,height = locateOnScreen("image.png")
        except:
            ImageNotFoundException
        click(x=x+width/2, y=y+height/2, clicks=1, button='left')
        hotkey("shift", "pgup")
        typewrite(["backspace"])
        typewrite(np.random.choice(["skibidi toilet", "No", "Stop", "Hey this is a family friendly groupchat buddy, watch ur language"]))
        hotkey("enter")
        click(x=700, y=100, clicks=1, button="left")
        time.sleep(10)
        click(x=1300, y=1200)
    else:
        time.sleep(10)