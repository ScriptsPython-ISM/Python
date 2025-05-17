import csv
import numpy as np
import re

class SuperBreak(Exception):
    pass

def replacer(s, newstring, index, nofail=False):
    if not nofail and index not in range(len(s)):
        raise ValueError("index outside given string")
    
    if index < 0:
        return newstring + s
    if index > len(s):
        return s + newstring
    
    return s[:index] + newstring + s[index + 1:]

with open("C:/Users/pmcgi/OneDrive/Desktop/Visual Studio/wordle/wordle.csv", newline='') as f:
    reader = csv.reader(f)
    words = [row[0].lower() for row in reader]
misplaced = {chr(i): set() for i in range(97,123)}
placements = r'.....'
alloweds = []
banned = r'[^\\]+'
guess = "crane"
try:
    for i in range(6):
        print(guess)
        result = input()
        if result == '33333':
            break
        for i, char in enumerate(guess):
            if result[i] == '3':
                placements = replacer(placements, char, i)
                alloweds.append(char)
            elif result[i] == '2':
                alloweds.append(char)
                misplaced[char].add(i)
            elif result[i] == '1':
                if char not in alloweds:
                    banned = replacer(banned, '^'+char, 1)
        guess = ""
        while True:
            if not words:
                print("No valid words left!")
                raise SuperBreak
            guess = np.random.choice(words)
            words.remove(guess)
            if not re.fullmatch(placements, guess):
                continue
            if not re.fullmatch(banned, guess):
                continue
            if any(char not in guess for char in alloweds):
                continue
            if any(i in misplaced[char] for i, char in enumerate(guess) if char in misplaced):
                continue
            break
except SuperBreak:
    pass