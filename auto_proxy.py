import requests

class AutoProxy():
	def __init__(self, proxy_type="socks4", timeout=10000, city="all"):
		self.proxy_type = proxy_type
		self.link = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=%s&timeout=%s&country=%s" % (proxy_type, str(timeout), city)
		self.proxy = []

	def load(self):
		self.proxy = [requests.get(self.link).text.split("")]

	@property
	def get(self):
		try:
			prox = self.proxy_type + "://" + self.proxy.pop()
			return dict(http=prox, https=prox)
		except Empty:
			print("Wait loading new proxy")
			self.load()
			return None