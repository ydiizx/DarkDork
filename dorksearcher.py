from bs4 import BeautifulSoup
from random import choice
from urllib.parse import urlparse
from os import system, name

import re
import threading
import queue
import requests
import time

print("Wait getting user agents..")
PROXYLINK = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=%s&timeout=%s&country=all&simplified=true"
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
prox_type = ['socks4', 'socks5', 'https']
errors = 0
valid = 0
valid_trash = 0
total_dork = 0
dork_usage = 0
clear = "clear" if name == "posix" else "cls"

def display():
	system(clear)
	print("DORK USAGE : ", dork_usage, "/", total_dork)
	print("VALID YAHOO: ", valid)
	print("VALID BING: ", valid_bing)
	print("FAILED : ", errors)
	print("VALID TRASH : ", valid_trash)

def load_prox(ids, proxy_chains=True):
	global q_proxy
	print("Reloading on ", ids)
	if proxy_chains:
		temp_proxy = dict(http="socks5://127.0.0.1:9050", https="socks5://127.0.0.1:9050")
		for p_type in prox_type:
			for x in requests.get(PROXYLINK % (p_type, "7000"), proxies=temp_proxy).text.split(): q_proxy.put_nowait(dict(http=p_type+"://"+x, https=p_type+"://"+x))
	else:
		for p_type in prox_type:
			for x in requests.get(PROXYLINK % (p_type, "7000")).text.split(): q_proxy.put_nowait(dict(http=p_type+"://"+x, https=p_type+"://"+x))

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
		global errors
		global dork_usage

		while True:
			prox = None
			try:
				prox = q_proxy.get(timeout=2)
			except queue.Empty:
				print("Empty")
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
			except Exception as e:
				print(e)

			if not prox:
				continue
			try:
				t = self.q.get(timeout=2)
				dork_usage += 1
			except queue.Empty:
				break

			ua = {'User-Agents': choice(USER_AGENTS)}
			a = None
			while not a:
				a = self.worker(t, ua, prox)
				if a == None:
					errors += 1
					try:
						prox = q_proxy.get(timeout=2)
					except queue.Empty:
						break
			display()
			self.q.task_done()

def check_link(link):
	if re.findall(TOP_DOMAIN, link):
		return True
	return False

def load_file(file_in, return_queue=False):
	global total_dork
	f = open(file_in, 'r', encoding='utf-8', errors='surrogateescape')

	if return_queue:
		q = queue.Queue()
		for x in f.readlines():
			total_dork += 1
			q.put_nowait(x.strip())
	else:
		q = list()
		for x in f.readlines(): q.append(x.strip())

	f.close()
	return q

def worker(query, ua, prox):
	pages = None
	r = None
	try:
		r = requests.get(YAHOO_URL+query, headers=ua, proxies=prox, timeout=8)
		r2 = requests.get(BING_URL+query, headers=ua, proxies=prox, timeout=8)
		if r.status_code == 500:
			print("Got blocked error!!")
			return
		elif r2.status_code == 500 and r2.status_code != 500:
			pass
		elif r2.status_code != 500 and r2.status_code == 500:
			pass
		else:
			return
	except Exception as e:
		return None
	except requests.exceptions.RequestException:
		return None
	except requests.exceptions.ConnectionError:
		return
	if not r and not r2:
		return
	elif not r and r2:
		pass
	elif r and not r2:
		pass
	else:
		return
	try:
		pages = parsing(r.text, first=True, method='yahoo')
		pages2 = parsing(r2.text, first=True, method="bing")
	except Exception as e:
		print("Error from worker yahoo:", e)
	if pages or pages2:
		temp = {"yahoo":pages, "bing":pages2}
		for page in temp:
			for pg in temp[page]:
				try:
					r = requests.get(pg, headers=ua).text
					parsing(r, method=page)
				except:
					continue
	return 1

def writer(link):
	#global file_out
	#global file_out_trash
	if check_link(link):
		return None
	if urlparse(link).query:
		f = open(file_out, 'a')
		f.write(link)
		valid += 1
	else:
		f = open(file_out_trash, 'a')
		f.write(link)
		valid_trash += 1
	f.close()

def parsing(resp=None, first=False, method=None):
	global valid_trash
	global valid

	pages = None
	soup = BeautifulSoup(resp, 'html.parser')

	if method == "yahoo":
		hrefs = soup.find_all('a', attrs={'class': 'ac-algo'})
		if first:
			try:
				pages = [x.attrs['href'] for x in soup.find('div', attrs={'class': 'pages'}).find_all('a')]
			except Exception as e:
				pass
	elif method == "bing":
		if "There are no results for" in resp:
			return None
		
		hrefs = soup.findAll('cite')
		if first:
			pages = soup.findAll('a', attrs={'class': 'b_widePage sb_bp'})
			if pages:
				pages = [x.attrs['href'] for x in pages]
	
	for link in hrefs:
		link = link.attrs['href'] if method == "yahoo" else link
		writer(link)
		
	if pages:
		return pages

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
