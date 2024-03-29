#coding:utf-8
from flask import Flask, render_template, request, redirect, url_for, Blueprint
from blockchain import exchangerates, statistics
from chart import chart
import urllib2, json, requests, datetime
import pandas as pd
import numpy as np
import scipy.stats

#Global variables
app = Flask(__name__)
app.register_blueprint(chart)
ticker = exchangerates.get_ticker()
stats = statistics.get()
actualpricelist = []
actualtimelist = []
actualpricelist_rev = []
actualtimelist_rev = []
actual = ['Actual Price']
date = ['Date']

#Chart section
jsonfilein = 'https://blockchain.info/charts/market-price?showDataPoints=false&timespan=&show_header=true&daysAverageString=1&scale=0&format=json&address='
r = requests.get(jsonfilein)
j = r.json()
entries = j['values']

#Def
def ccylists():
	return ticker

def ccyprice():
	for k in ticker:
		yield ticker[k].p15min

def ccysymbol():
	for s in ticker:
		yield ticker[s].symbol

def ccyset():
	for k in ticker:
		return k, ticker[k].symbol, ticker[k].p15min

def actualprice():
	for e in entries:
		yield e['y']

def actualtime():
	for e in entries:
		yield datetime.datetime.fromtimestamp(int(e['x'])).strftime('%Y-%m-%d')

def predictionprice():
	for e in entries:
		yield e['y']

def predictiontime():
	for e in entries:
		yield e['x']

#Flask view
@app.route('/')
def index():
	return render_template('index.html', title=title)

@app.route('/chart')
def chart():
	actualpricelist = []
	actualtimelist = []
	actualpricelist_rev = []
	actualtimelist_rev = []
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt)

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)
	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]

	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/chart3')
def chart3():
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev[:3]
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev[:3]
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt) # + 172800

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev[:3]

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime[:3]

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)

	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]


	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/chart7')
def chart7():
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev[:7]
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev[:7]
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt) # + 518400

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev[:7]

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime[:7]

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)

	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]

	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/chart15')
def chart15():
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev[:15]
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev[:15]
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt) # + 1209600

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev[:15]

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime[:15]

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)

	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]

	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/chart30')
def chart30():
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev[:30]
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev[:30]
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt) # + 2505600

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev[:30]

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime[:30]

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)

	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]

	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/chart60')
def chart60():
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev[:60]
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev[:60]
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt) # + 5097600

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev[:60]

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime[:60]

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)

	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]

	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/chart90')
def chart90():
	predictiontimelist = []
	predictiontimelist_rev = []
	predictiontimelist_rev_decoded = ['PDate']

	for ap in actualprice():
		actualpricelist_rev.append(ap)

	actualpricelist_rev.reverse()
	aplrev = actualpricelist_rev[:90]
	apl = actual + aplrev
	ppl = pd.Series(aplrev)

	for t in actualtime():
		actualtimelist_rev.append(t)

	actualtimelist_rev.reverse()
	atrev = actualtimelist_rev[:90]
	atl = date + atrev

	for pt in predictiontime():
		predictiontimelist_rev.append(pt) # + 7689600

	predictiontimelist_rev.reverse()
	ptrev = predictiontimelist_rev[:90]

	traintime = [] #Actual unix time for train data
	traintimelist = [] #Actual unix time for train data
	for tt in predictiontime():
		traintime.append(tt)
	traintime.reverse()
	traintimelist = traintime[:90]

	ptl = pd.Series(traintimelist)

	for timedecode in ptrev:
		predictiontimelist_rev_decoded.append(datetime.datetime.fromtimestamp(int(timedecode)).strftime('%Y-%m-%d'))

#Pandas linear regression prediction model
	model = pd.ols(y=ppl, x=ptl)

	modelx = model.beta['x']
	modelintercept = model.beta['intercept']

#Price from linear reg
	predictionpricelist = [utime * modelx + modelintercept for utime in ptrev]
	predictionpricelist.insert(0,'Linear Regression')

#RSI Chart
	rsipricelist = []
	for rp in actualprice():
		rsipricelist.append(rp)
	for t in actualtime():
		actualtimelist.append(t)

	rsifirstdate = actualtimelist[14] #For reference, not to use

#RSI Calculation
	rsilist = ['RSI 14'] #Array For JS
	rsicount = 1 #Initialize
	listhead = 0 #Get 15 values JIC
	listtail = 14

	for calcrsi in rsipricelist:
		if rsicount < 354:
			calclist = rsipricelist[listhead:listtail] #Pricelist array for RSI
			pluslist = []
			minuslist = []
			rsix = 0
			rsiy = 1
			for i in xrange(14): #RSI calc start
				if rsiy < 14:
					rsia = calclist[rsix]
					rsib = calclist[rsiy]
					rsiz = rsib - rsia
					if rsiz > 0.0:
						pluslist.append(rsiz)
					else:
						minuslist.append(-rsiz)
					rsix += 1
					rsiy += 1
			avggain = sum(pluslist) / 14.0
			avgloss = sum(minuslist) / 14.0
			rsia = 0
			rsib = 0
			rsiz = 0
			rs = avggain / avgloss
			rsi = 100 - 100 / (1 + rs)
			rsilist.append(rsi)
			rsicount += 1 #Increment count for next for-paragraph
			listhead += 1
			listtail += 1
			del pluslist[:] #Initialize all lists that works for only python 2.7
			del minuslist[:]

	return render_template('chart.js', rsilist=rsilist, predictionpricelist=predictionpricelist, predictiontime=predictiontimelist_rev_decoded, modelx=modelx, modelintercept=modelintercept, actualtime=atl, actualprice=apl)

@app.route('/jpy', methods=['GET', 'POST'])
def jpy():
	title = 'JPY Simple Converter'
	name = request.form['name']
	btc_amo = exchangerates.to_btc('JPY', name)
	home = redirect(url_for('index'))
	excsym = ticker['JPY'].symbol
	excrat = ticker['JPY'].p15min
	priceList = []
	for item in ccyprice():
		priceList.append(item)
	usdmktprice = stats.market_price_usd
	return render_template('index.html', usdmktprice=usdmktprice, excrat=excrat, excsym=excsym, home=home, name=name, btc_amo=btc_amo, ccyprice=priceList, ccylists=ccylists(), title=title)

#Conf
# if __name__ == '__main__':
# 	app.debug = True
# 	app.run(host='0.0.0.0')
