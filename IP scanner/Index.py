
import argparse
import ipaddress
import json
import socket
import time
import urllib.parse
from collections import defaultdict
import netifaces
from prettytable import PrettyTable
from scapy.all import ARP, Ether, srp
import nmap
from zeroconf import Zeroconf, ServiceBrowser
from zeroconf._exceptions import BadTypeInNameException
from ssdpy import SSDPClient

def get_default_subnet():
    gw = netifaces.gateways()['default'][netifaces.AF_INET][0]
    netmask = netifaces.ifaddresses(netifaces.gateways()['default'][netifaces.AF_INET][1])[netifaces.AF_INET][0]['netmask']
    return str(ipaddress.ip_network(f"{gw}/{netmask}", strict=False))

def arp_scan(subnet):
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp = ARP(pdst=subnet)
    ans = srp(ether/arp, timeout=2, retry=1, verbose=False)[0]
    return {r.psrc: {"mac": r.hwsrc, "methods": ["ARP"]} for _, r in ans}

def nmap_ping(subnet):
    nm = nmap.PortScanner()
    nm.scan(hosts=subnet, arguments="-sn -n -T4")
    return {h: {"mac": nm[h]['addresses'].get('mac'), "methods": ["NMAP"]} for h in nm.all_hosts()}

def mdns_scan(timeout=5):
    devices = {}
    class Listener:
        def add_service(self, zc, t, name):
            try:
                info = zc.get_service_info(t, name)
            except BadTypeInNameException:
                return
            if info and info.addresses:
                ip = socket.inet_ntoa(info.addresses[0])
                devices.setdefault(ip, {"methods": []})
                devices[ip]["name"] = name.split("._")[0]
                devices[ip]["methods"].append("mDNS")
        def update_service(self, zc, t, name):
            pass
    zc = Zeroconf()
    ServiceBrowser(zc, "_services._dns-sd._udp.local.", Listener())
    time.sleep(timeout)
    zc.close()
    return devices

def ssdp_scan():
    client = SSDPClient()
    responses = client.m_search("ssdp:all")
    out = {}
    for d in responses:
        loc = d.get("location") or d.get("LOCATION") or d.get("Location")
        if not loc:
            continue
        host = urllib.parse.urlparse(loc).hostname
        if not host:
            continue
        out.setdefault(host, {"methods": []})
        out[host]["location"] = loc
        out[host]["methods"].append("SSDP")
    return out

def merge_dicts(dicts):
    merged = defaultdict(lambda: {"methods": []})
    for d in dicts:
        for ip, info in d.items():
            merged[ip]["methods"] = list(set(merged[ip]["methods"]) | set(info.get("methods", [])))
            for k, v in info.items():
                if k != "methods" and v and not merged[ip].get(k):
                    merged[ip][k] = v
    return merged

def reverse_dns_lookup(results):
    for ip, info in results.items():
        if not info.get("name"):
            try:
                name = socket.gethostbyaddr(ip)[0]
                info["name"] = name
                info.setdefault("methods", []).append("DNS")
            except:
                pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--subnet")
    parser.add_argument("-j", "--json", action="store_true")
    args = parser.parse_args()
    subnet = args.subnet or get_default_subnet()
    print(f"[+] Scanning subnet {subnet}")
    print("[*] Performing ARP scan...")
    arp = arp_scan(subnet)
    print(f"    ARP found {len(arp)} hosts")
    print("[*] Performing Nmap ping scan...")
    nmap_res = nmap_ping(subnet)
    print(f"    Nmap found {len(nmap_res)} hosts")
    print("[*] Performing mDNS scan...")
    mdns = mdns_scan()
    print(f"    mDNS found {len(mdns)} services")
    print("[*] Performing SSDP scan...")
    ssdp = ssdp_scan()
    print(f"    SSDP found {len(ssdp)} devices")
    results = merge_dicts([arp, nmap_res, mdns, ssdp])
    reverse_dns_lookup(results)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        table = PrettyTable(["IP", "MAC", "Name", "Location", "Methods"])
        for ip, info in results.items():
            table.add_row([
                ip,
                info.get("mac", ""),
                info.get("name", ""),
                info.get("location", "")[:40] if info.get("location") else "",
                ",".join(sorted(info["methods"]))
            ])
        print(table)

if __name__ == "__main__":
    main()
