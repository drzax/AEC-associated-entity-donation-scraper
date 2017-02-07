#!/usr/bin/env python
#Scraper for donations declared by associated entities

import csv
import mechanize 
import lxml.html
import scraperwiki
import requests
import traceback
 
annDonorsurl = "http://periodicdisclosures.aec.gov.au/AnalysisAssociatedEntity.aspx"
 
periods = [
{"year":"2012-2013","id":"51"},
{"year":"2013-2014","id":"55"},
{"year":"2014-2015","id":"56"},
{"year":"2015-2016","id":"60"}	
]

# periods = [{"year":"2014-2015","id":"56"}]

#Check if scraper has been run before, see where it got up to

if scraperwiki.sqlite.get_var('upto'):
	upto = scraperwiki.sqlite.get_var('upto')
	print "Scraper upto:",upto,"period:",periods[upto]['year']
else:
	print "Scraper first run"
	upto = 0    

#to run entirely again, just set upto to 0 
# upto = 0  


for x in xrange(upto, len(periods)):
	br = mechanize.Browser()
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	response = br.open(annDonorsurl)
	print "Loading data for "+periods[x]['year']

	br.select_form(nr=0)
	# for i,form in enumerate(br.forms()):
	#     print i
	#     print form
 
	br['ctl00$dropDownListPeriod']=[periods[x]['id']]
	response = br.submit("ctl00$buttonGo")

	response = br.open(annDonorsurl)
	br.select_form(nr=0)

	items = br.form.controls[10].get_items()

	for item in items:
                # unique number for every entry (per entity per year) to avoid issues with very similar donations
                # and make it possible to re-run with different years enabled without messing up the DB.
                count = 0
		print item.name
		print "Entity:", item.attrs['label']

		response = br.open(annDonorsurl)
		br.select_form(nr=0)
		br['ctl00$ContentPlaceHolderBody$dropDownListEntities']=[item.name]
		response = br.submit("ctl00$ContentPlaceHolderBody$analysisControl$buttonAnalyse")

		html = response.read()
		root = lxml.html.fromstring(html)
		tds = root.cssselect("#ContentPlaceHolderBody_gridViewAnalysis tr td")
		
		if tds[0].text == "There have been no receipts reported":
			print tds[0].text
			continue

		br.select_form(nr=0)
		br['ctl00$ContentPlaceHolderBody$pagingControl$cboPageSize']=["500"]
		response = br.submit("ctl00$ContentPlaceHolderBody$pagingControl$buttonGo")

		# Check if any donations

		html = response.read()
		root = lxml.html.fromstring(html)
		trs = root.cssselect("#ContentPlaceHolderBody_gridViewAnalysis tr")
	
		for tr in trs[1:]:
			tds = tr.cssselect("td")
			#print lxml.html.tostring(tds[0])
			donType = lxml.html.tostring(tds[0]).split('<a href="')[1].split('.aspx?')[0]
			#print donType
			submissionID = lxml.html.tostring(tds[0]).split('SubmissionId=')[1].split('&amp;ClientId=')[0]
			#print submissionID
			clientID = lxml.html.tostring(tds[0]).split('ClientId=')[1].split('">')[0]
			#print clientID
			donName = lxml.html.tostring(tds[0]).split('">')[2].split('</a')[0]
			#print donName
			address = tds[1].text
			#print address
			state = tds[2].text
			#print state
			postcode = tds[3].text
			#print postcode
			receiptType = tds[4].text
			#print receiptType
			value = tds[5].text.replace("$", "").replace(",","")
			#print value
			donUrl = lxml.html.tostring(tds[0]).split('<a href="')[1].split('">')[0]
			#print donUrl 


			fixedUrl = 'http://periodicdisclosures.aec.gov.au/' + donUrl.replace("amp;","")
			html = requests.get(fixedUrl).content
			dom = lxml.html.fromstring(html)
			h2s = dom.cssselect(".rightColfadWideHold h2")
			if donType == "Donor" or donType == "AssociatedEntity":
				cleanName = h2s[0].text.strip()
				#print cleanName.strip()
			if donType == "Party":
				cleanName = h2s[1].text.strip()
				#print cleanName.strip()

			count += 1
			data = {}
			data['donType'] = donType
			data['submissionID'] = submissionID
			data['clientID'] = clientID
			data['donName'] = donName
			data['address'] = address
			data['state'] = state
			data['postcode'] = postcode
			data['receiptType'] = receiptType
			data['value'] = value
			data['donUrl'] = donUrl
			data['count'] = count
			data['entityID'] = item.name
			data['period'] = periods[x]['year']
			data['entityName'] = item.attrs['label']
			data['cleanName'] = cleanName

			if data:
# 				print data
				scraperwiki.sqlite.save(unique_keys=["count","donUrl","period"], data=data)
