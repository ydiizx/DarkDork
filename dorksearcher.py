from bs4 import BeautifulSoup
from random import choice
from urllib.parse import urlparse

import re
import threading
import queue
import requests
import time

print("Wait getting user agents..")
PROXYLINK = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=80&country=all&simplified=true"
YAHOO_URL = "https://search.yahoo.com/search?p="
BING_URL = "https://www.bing.com/search?q="
USER_AGENTS = list()
TOP_DOMAIN = list()

with open('user-agents.txt', 'r') as f:
	USER_AGENTS = [x.strip() for x in f.readlines()]

with open('topdomain.txt', 'r') as f:
	TOP_DOMAIN = "|".join([x.strip() for x in f.readlines()])

q_proxy = queue.Queue()
onload = False

def load_prox(ids):
	global q_proxy
	print("Reloading on ", ids)
	for x in requests.get(PROXYLINK).text.split(): q_proxy.put_nowait(dict(http="socks4://"+x, https="socks4://"+x))
	# print("Get proxy")

class Worker(threading.Thread):
	def __init__(self, q, yahoo, ids,	 *args, **kwargs):
		self.q = q
		self.yahoo = yahoo
		self.ids = ids
		super().__init__(*args, **kwargs)
		self._lock = threading.Lock()
		self._event = threading.Event()

	def run(self):
		global onload
		global q_proxy

		while True:
			try:
				prox = q_proxy.get(timeout=2)
			except queue.Empty:
				with self._lock:
					if not onload:
						time.sleep(1)
						if not onload:
							onload = True
							# print("onload = ", onload, "ids = ", self.ids)
							load_prox(self.ids)
							onload = False
					else:
						self._event.clear()
						# print("Waiting ", onload, "ids : ", self.ids)
						self._event.wait(5.0)
						self._event.set()
						# print("Done Waiting")
						continue
			try:
				t = self.q.get(timeout=2)
			except queue.Empty:
				break

			ua = {'User-Agents': choice(USER_AGENTS)}
			a = None
			while not a:
				a = self.yahoo(t, ua, prox)
				if a == None:
					print("Failed Proxy", prox['http'])
			# self.bing(t, ua)
			self.q.task_done()

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
	# while True:
	r = None
	try:
		r = requests.get(YAHOO_URL+query, headers=ua, proxies=prox, timeout=10)
		if r.status_code == 500:
			print("Got blocked error!!")
			return

	except Exception as e:
		# print(e)
		return None
		# continue
	except requests.exceptions.RequestException:
		return None
	except requests.exceptions.ConnectionError:
		return

	if not r:
		return
	
	try:
		pages = parsing(r.text, first=True, method='yahoo')
	except Exception as e:
		print("Error from worker yahoo:", e)

	if pages:
		for page in pages:
			try:
				r = requests.get(page, headers=ua).text
				parsing_yahoo(r, method='yahoo')
			except:
				continue
	return 1

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
			# print("From yahoo => ")
			if urlparse(link).query:
				f = open(file_out, 'a')
			else:
				f = open(file_out_trash, 'a')
			
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

def worker_bing(query, ua):
	bing_url = BING_URL + query
	next_page = None
	try:
		r = requests.get(bing_url, headers=ua)
		if r.status_code == 500:
			print("Gots blocked from bing...")
			return
		next_page = parsing(r.text, first=True, method="bing")
	except Exception as e:
		print("BIng Error => ", e)
	if next_page:
		for i in next_page:
			try:
				r = requests.get(bing_url+i, headers=ua)
				if r.status_code == 500:
					print("Gots blocked from bing...")
					return
				parsing(r.text, method="bing")
			except Exception as e: print("Bing Error 2 => ", e)

def dork_searcher(file_in, threads):
	q = load_file(file_in, return_queue=True)

	for i in range(threads):
		Worker(q, worker_yahoo, i).start()

	q.join()
	print("DONE")

if __name__ == '__main__':
	from sys import argv
	if len(argv) < 2:
		print("Usage: %s file_in.txt file_out.txt threads" % argv[0])
		exit()
	global file_out
	global file_out_trash

	file_out = argv[2]
	if "/" in file_out:
		file_out_trash = "/".join(file_out.split("/")[:-1]) + "/" + 'trash_'+file_out.split("/")[-1]
	else:
		file_out_trash = 'trash_' + file_out
	load_prox(0)
	dork_searcher(argv[1], int(argv[3]))