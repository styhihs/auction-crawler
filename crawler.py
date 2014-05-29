# -*- coding: utf-8 -*-
import os
import re
import datetime
import urllib2
from bs4 import BeautifulSoup
from lxml import etree as ET
from time import sleep

def get_current_time():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_content(url):
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


def crawler():
	url = 'https://tw.bid.yahoo.com/tw/23000-allsubcats.html?.r=1400475784'
	#header = ('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.66 Safari/537.36 LBBROWSER')
	#opener = urllib2.build_opener()
	#opener.addheaders = [header]

	try:
		#html = opener.open(url).read()
		html = urllib2.urlopen(url).read()
	except:
		print '*** Access error ' + url



	soup = BeautifulSoup(html, 'html5lib')
	links = soup.find_all('a', class_ = 'title')
	
	targets = []
	categories = []
	pattern = re.compile('-category-leaf')
	for link in links:
		l = str(link['href'])
		cat = link.get_text()
		if pattern.search(l) != None:
			targets.append(l)
			categories.append(cat)

	count = 0
	for index, target in enumerate(targets):
		if count < 3:
			print 'start ' + categories[index]
			root = ET.Element('auction')
			head = ET.SubElement(root, 'head')
			body = ET.SubElement(root, 'body')
			site = ET.SubElement(head, 'website')
			site.text = u'Yahoo!奇摩拍賣'
			cat = ET.SubElement(head, 'category')
			cat.text = u'女裝與服飾配件'
			subcat = ET.SubElement(head, 'subcategory')
			subcat.text = categories[index]
			date = ET.SubElement(head, 'date')
			date.text = get_current_time()

			#html = urllib2.urlopen(target).read()
			#soup = BeautifulSoup(html, 'html5lib')
			#link = soup.find('span', text = '出價次').parent['href']
			#page_url = 'https://tw.bid.yahoo.com/tw/' + link

			page_url = target
			
			cnt = 0	
			suc_cnt = 0
			print 'Start crawling ' + categories[index] + '....'
			while cnt < 50 and page_url != 'https://tw.bid.yahoo.com/tw/':
				try:
					html = urllib2.urlopen(page_url).read()
				except:
					print '### Access error ' + target
					continue

				soup = BeautifulSoup(html, 'html5lib')
				links = soup.find_all('div', class_ = 'srp-pdtitle ellipsis')
				for link in links:
					l = str(BeautifulSoup(str(link), 'html5lib').find('a')['href'])
					if re.search('auction', l) != None:		# 避開 yahoo 商城
						product = extract_content(l)

						if product != 'error':
							item = ET.SubElement(body, 'item')
							name = ET.SubElement(item, 'name')
							name.text = product['name']
							time = ET.SubElement(item, 'time')
							time.text = product['time']
							price = ET.SubElement(item, 'price')
							price.text = product['price']
							amount = ET.SubElement(item, 'amount')
							amount.text = product['amount']
							suc_cnt += 1

					cnt += 1
					if cnt >= 30:
						break
					sleep(1)

				# --- find next page ---
				next_page = soup.find('li', class_ = 'next-page yui3-u').find('a')['href']
				page_url = 'https://tw.bid.yahoo.com/tw/' + next_page

			total = ET.SubElement(head, 'total')
			total.text = str(suc_cnt)
			print categories[index] + ' done....'
			tree = ET.ElementTree(root)
			tree.write(categories[index] + '.xml', encoding = 'utf-8', xml_declaration = True, pretty_print = True)
			count += 1


if __name__ == '__main__':
	crawler()