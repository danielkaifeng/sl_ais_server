#coding=utf-8
import urllib2 
import httplib2 
import urllib
from poster.streaminghttp import register_openers 
import json
import re
import os
import numpy as np

def send_post_request(post_url, req_json):
		register_openers()
		headers = {'Content-Type': 'application/json'}
		req_json= json.dumps(req_json)

		req = urllib2.Request(url=post_url, headers=headers, data=req_json)

		res = urllib2.urlopen(req).read()
		
		return res

if __name__ == "__main__":
		url = "http://192.168.9.60:6500/get_ecg_disease_classification"
		#url = "http://www.iiecg.com:6500/get_prediction"

		data = np.random.random(15582) * 2000
		req_json = {"ssid": "hi", "ecgdata": data.tolist()}
		res = send_post_request(url, req_json)
		print res


