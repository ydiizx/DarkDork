from bs4 import BeautifulSoup
from random import choice

import re
import threading
import queue
import requests

print("Wait getting user agents..")
USER_AGENTS = requests.get("https://gist.githubusercontent.com/pzb/b4b6f57144aea7827ae4/raw/cf847b76a1GvzmW4PDo92bw6KoGSzTuynHTPJRVpHL6/user-agents.txt").text.split("\n")
TOP_DOMAIN = "|".join(requests.get("https://gist.githubusercontent.com/jgamblin/62fadd8aa321f7f6a482912a6a317ea3/raw/36EkRHLyviZMtSjodB4gByQJwyYxPmBE1x/urls.txt").text.split("\n"))
YAHOO_URL = "https://search.yahoo.com/search?p="
BING_URL = "https://www.bing.com/search?q="
CHECK_PROXY_URL = "https://api.ipify.org"

class AutoProxy():
	def __init__(self, proxy_type="socks4", timeout=10000, city="all"):
		self.proxy_type = proxy_type
		self.link = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=%s&timeout=%s&country=%s" % (proxy_type, str(timeout), city)
		self.empty = False
		self.proxy = []

	def load(self):
		print("Loading proxy")
		self.proxy = requests.get(self.link).text.split()
		print("DONE")

	@property
	def get(self):
		if not self.proxy:
			return dict(http="socks5://127.0.0.1:9050", https="socks5://127.0.0.1:9050") # default proxychains
		try:
			prox = self.proxy_type + "://" + self.proxy.pop()
			return dict(http=prox, https=prox)
		except IndexError:
			self.empty = True
			return False

class Worker(threading.Thread):
	def __init__(self, q, bing, yahoo, *args, **kwargs):
		self.q = q
		self.yahoo = yahoo
		self.bing = bing
		self.proxy = None
		super().__init__(*args, **kwargs)

	def run(self):
		while True:
			try:
				t = self.q.get(timeout=2)
			except queue.Empty:
				break
			ua = {'User-Agents': choice(USER_AGENTS)}
			if not self.proxy and not proxer.empty:
				while not self.proxy:
					self.proxy = check_proxy(proxer.get)

			if proxer.empty and not self.proxy:
				self.proxy = dict(http="socks5://127.0.0.1:9050", https="socks5://127.0.0.1:9050")

			p1 = self.yahoo(t, ua, self.proxy)
			p2 = self.bing(t, ua, self.proxy)

			if (not proxer.empty and (p1 == 0 or p2 == 0)):
				self.proxy = None
				while not self.proxy:
					self.proxy = check_proxy(proxer.get)

			self.q.task_done()

def check_proxy(prox):
	if prox:
		try:
			gt = requests.get(CHECK_PROXY_URL, proxies=prox)
			print("LIVE :",gt.text)
			return prox
		except requests.exceptions.Timeout:
			return False

	return False

def check_link(link):
	if re.findall(TOP_DOMAIN, link):
		return True
	return False

def load_file(file_in, return_queue=False):
	f = open(file_in, 'r', encoding='utf-8', errors='surrogateescape')
	
	if return_queue:
		q = queue.Queue()
		for x in f.readlines(): q.put_nowait(x.strip())
	else:
		q = list()
		for x in f.readlines(): q.append(x.strip())

	f.close()
	return q

def worker_yahoo(query, ua, prox):
	pages = None
	try:
		r = requests.get(YAHOO_URL+query, headers=ua, proxies=proxy)
		if r.status_code == 500:
			print("Got blocked error!!")
			return
	except IOError:
		return 0
	except:
		return
	try:
		pages = parsing(r.text, first=True, method='yahoo')
	except Exception as e:
		print("Error from worker yahoo:", e)

	if pages:
		for page in pages:
			try:
				r = requests.get(page, headers=ua, proxies=proxy).text
				parsing_yahoo(r, method='yahoo')
			except:
				continue
	return 0

def parsing(resp=None, first=False, method=None):
	pages = None
	soup = BeautifulSoup(resp, 'html.parser')
	
	if method == "yahoo":
		hrefs = soup.find_all('a', attrs={'class': 'ac-algo'})
		if first:
			try:
				pages = [x.attrs['href'] for x in soup.find('div', attrs={'class': 'pages'}).find_all('a')]
			except Exception as e:
				
				# print(" error method yahoo:", e)
				pass
		for link in hrefs:
			link = link.attrs['href']
			if check_link(link):
				continue
			print("From yahoo => ", link)
			f = open(file_out, 'a')
			f.write(link+'\n')
			f.close()

		return None
	elif method == "bing":
		if "There are no results for" in resp:
			return None

		cite = soup.findAll('cite')
		if len(cite) >=4:
			for x in cite:
				try:
					if check_link(x):
						continue
					print("From bing =>", x.text)
					f = open(file_out, 'a')
					f.write(x.text+'\n')
					f.close()
				except Exception as e:
					print(e)
					continue
		if first:
			pages = soup.findAll('a', attrs={'class': 'b_widePage sb_bp'})
			print(pages)
			if pages:
				pages = [x.attrs['href'] for x in pages]

	if pages:
		return pages

def worker_bing(query, ua, proxy):
	bing_url = BING_URL + query
	next_page = None
	try:
		r = requests.get(bing_url, headers=ua, proxies=proxy)
		if r.status_code == 500:
			print("Gots blocked from bing...")
			return
		next_page = parsing(r.text, first=True, method="bing")
	except IOError:
		return 0
	except requests.exceptions.Timeout:
		return False
	except Exception as e:
		print("BIng Error => ", e)
	if next_page:
		for i in next_page:
			try:
				r = requests.get(bing_url+i, headers=ua, proxies=proxy)
				if r.status_code == 500:
					print("Gots blocked from bing...")
					return
				parsing(r.text, method="bing")
			except Exception as e: print("Bing Error 2 => ", e)

def dork_searcher(file_in, threads):
	q = load_file(file_in, return_queue=True)

	for _ in range(threads):
		Worker(q, worker_bing, worker_yahoo).start()

	q.join()

	print("DONE")

if __name__ == '__main__':
	from sys import argv
	if len(argv) < 2:
		print("Usage: %s file_in.txt file_out.txt threads" % argv[0])
		exit()
	global file_out
	file_out = argv[2]
	proxer = AutoProxy()
	proxer.load()
	dork_searcher(argv[1], int(argv[3]))