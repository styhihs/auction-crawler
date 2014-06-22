# -*- coding: utf-8 -*-
import os
import re
import datetime
import urllib2
from bs4 import BeautifulSoup
from lxml import etree as ET
from time import sleep

class AuctionItem:
	def __init__(self, category):
		self.root = ET.Element('auction')
		self.head = ET.SubElement(self.root, 'head')
		self.body = ET.SubElement(self.root, 'body')
		site = ET.SubElement(self.head, 'website')
		site.text = u'Yahoo!奇摩拍賣'
		cat = ET.SubElement(self.head, 'category')
		cat.text = u'女裝與服飾配件'
		subcat = ET.SubElement(self.head, 'subcategory')
		subcat.text = category
		date = ET.SubElement(self.head, 'date')
		date.text = get_current_time()

	def add_item(self, name, finish_time, price, sold_amount):
		item = ET.SubElement(self.body, 'item')
		item_name = ET.SubElement(item, 'name')
		item_name.text = name
		#item_time = ET.SubElement(item, 'time')
		#item_time.text = finish_time
		item_price = ET.SubElement(item, 'price')
		item_price.text = price
		item_amount = ET.SubElement(item, 'amount')
		item_amount.text = sold_amount

	def add_total(self, num):
		total = ET.SubElement(self.head, 'total')
		total.text = str(num)

	def get_root(self):
		return self.root


def get_current_time():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_content_mall(url, headers):
	p_info = {}

	request = urllib2.Request(url, None, headers)

	try:
		response = urllib2.urlopen(request)
	except urllib2.URLError as e:
		print '*** Access error ***'
		print e.reason
		return 'error'

	html = response.read()

	soup = BeautifulSoup(html, 'html5lib')
	p_info['name'] = soup.find('span', {'itemprop': 'name'}).get_text()
	p_info['price'] = soup.find('span', {'itemprop': 'price'}).get_text()[:-1]
	amount = soup.find('li', text = re.compile(u'銷售件數：'))
	if not (amount is None):
		p_info['amount'] = amount.get_text()[4:]
	else:
		p_info['amount'] = 'N/A'

	return p_info

'''
def extract_content_auction(url):
	p_info = {}

	try:
		html = urllib2.urlopen(url).read()
	except:
		print '***Access error ' + url
		return 'error'

	soup = BeautifulSoup(html, 'html5lib')
	p_info['name'] = soup.find('span', {'itemprop': 'name'}).get_text()
	info_html = soup.find('ul', class_ = 'inf')
	p_info['time'] = soup.find('span', text = '開始時間：').find_next_sibling(text = True)
	p_info['price'] = soup.find('span', text = '目前出價：').find_next_sibling('strong').get_text()
	p_info['amount'] = soup.find('span', text = '出價次數：').find_next_sibling(text = True)
	pattern = re.compile(r'[ \n\r\t\f]')
	p_info['amount'] = pattern.sub('', p_info['amount'])

	return p_info
'''

def crawler(target_url, headers):
	request = urllib2.Request(target_url, None, headers)

	try:
		response = urllib2.urlopen(request)
	except urllib2.URLError as e:
		print '*** Access error ***'
		print e.reason

	html = response.read()

	soup = BeautifulSoup(html, 'html5lib')
	links = soup.find_all('a', class_ = 'title')
	
	# Retrieve all needed out-links in the target_url
	targets = []	# category urls
	categories = []	# category names
	pattern = re.compile('-category-leaf')
	for link in links:
		l = str(link['href'])
		cat = link.get_text()
		if pattern.search(l) != None:
			targets.append(l + '&sort=-bidcnt')
			categories.append(cat)

	for index, target in enumerate(targets):
		# Build xml structure
		items_root = AuctionItem(categories[index])
		items_total = 0

		page_url = target
		mycnt = 0
		print 'Start crawling ' + categories[index] + '....'
		while page_url != 'https://tw.bid.yahoo.com/tw/':
			request = urllib2.Request(page_url, None, headers)
			try:
				response = urllib2.urlopen(request)
			except urllib2.URLError as e:
				print '*** Access error ***'
				print e.reason
				continue

			html = response.read()

			soup = BeautifulSoup(html, 'html5lib')
			items = soup.find_all('div', class_ = 'yui3-u srp-pdcontent')
			for item in items:
				title_sec = item.find('div', class_ = 'srp-pdtitle ellipsis')
				link = str(title_sec.find('a')['href'])		# item's link

				if re.search('auction', link) != None:
					# yahoo 拍賣項目
					title = title_sec.get_text().strip()
					price = item.find('div', class_ = 'yui3-u div1').find('em').get_text()
					amount = item.find('span', class_ = 'div2 yui3-u').find('span').get_text()
					if amount == '-':
						amount = '0'
					items_root.add_item(title, None, price, amount)
					items_total += 1

				else:
					# yahoo 超級商城項目
					continue	# 先跳過
					'''
					prod = extract_content_mall(link, headers)

					if prod != 'error':
						items_root.add_item(prod['name'], None, prod['price'], prod['amount'])
						items_total += 1

					# still need to find the appropriate delay interval.....
					sleep(3)
					'''

			sleep(1)

			# count crawled pages
			mycnt += 1
			print 'page#' + str(mycnt) + ' done'
			if mycnt >= 5:	# number of pages to be crawled
				break

			# --- find next page ---
			tag = soup.find('li', class_ = 'next-page yui3-u')
			if not (tag is None):
				next_page = tag.find('a')['href']
			page_url = 'https://tw.bid.yahoo.com/tw/' + next_page

		items_root.add_total(items_total)
		print categories[index] + ' done....'
		tree = ET.ElementTree(items_root.get_root())
		tree.write('./data/' + str(index) + '_' + categories[index] + '.xml', encoding = 'utf-8', xml_declaration = True, pretty_print = True)


if __name__ == '__main__':
	target_url = 'https://tw.bid.yahoo.com/tw/23000-allsubcats.html?.r=1400475784'
	user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36'

	headers = {'User-Agent': user_agent}
	crawler(target_url, headers)