# server.py
##coding=utf-8
import time
import zmq
import json
import os
import math

import sys
#reload(sys) 
#sys.setdefaultencoding('utf-8')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


from flask import Flask
from flask import request
from flask import make_response
from flask_cors import CORS
import datetime

#from update_mongoDB import update_record
from predict import *
from predict_mul_disease import *

from idx_rule import filter_idx

app = Flask(__name__)
CORS(app, supports_credentials=True, methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"], allow_headers='*')

pb_filepath = "protobuf/lb_single_lead_2100_TP0.936667_FP0.990000.pb" 

sess = load_graph(pb_filepath)
sess2, version = load_graph2()
print "noise algorithm version: " + version

symp_idx_dict, aha_dict, if_show, app_key = get_symp_idx_dict("symp_code.csv")

def search_longest_middle_seq(ecg):
		len_count = [len(x) for x in ecg]
		seq = ecg[np.argmax(len_count)]

		start_idx = (len(seq) - 5120)//2
		opt_seq = seq[start_idx:start_idx+5120]

		return opt_seq

def fcn_filter(ecg_x):
		print "ecg_x shape:", len(ecg_x)
		remainder = len(ecg_x) % 32
		if remainder != 0 :
				print "\ncut remainder~~~~~~~~~~~~~\n"
				ecg_x = ecg_x[:len(ecg_x)-remainder]

		print "ecg_x shape:", len(ecg_x)
		test_x = normalization(ecg_x)
		print "test_x shape:", len(test_x)
		disease_class = inference2(sess2, np.array([test_x]))
		print np.unique(disease_class)

		clean_ecg = get_clean_ecg(ecg_x, disease_class[0])
		if len(clean_ecg) > 0:
			#return clean_ecg[0][:5120]
			opt_seq = search_longest_middle_seq(clean_ecg)
			return opt_seq
		else:
			return None

def get_app_dict(symp_code, app_key):
		symp_data = {}

		for k in app_key:
			if k == '0':
				if k in symp_code:
					#status_flag = True
					status_flag = False
				else:
					status_flag = True
			#elif k in symp_code or k == 'I48' or k=='I45.102':
			elif k in symp_code:
					symp_data[k] = 1
			else:
					symp_data[k] = 0
	
		return symp_data, status_flag

def process_data(req_dict):
		ssid = req_dict['ssid'].strip()
		origin_x = req_dict['ecgdata']
		origin_x = np.array(origin_x)
		print origin_x

		# 取10秒无噪音的数据准备进入模型
		#ecg_x = origin_x[5120:5120*2]
		ecg_x = fcn_filter(origin_x)			

		bad_quality_flag = 0
		if ecg_x is not None:
				ecg_x = np.float32(ecg_x)
				ecg_x /= 1000.
				np.savetxt("received_ecg", ecg_x, fmt="%f", delimiter=',')
				ecg_x = np.reshape(ecg_x, [-1,1])

				# 数据进模型得到预测值
				pre_y = inference([ecg_x], sess)
				print pre_y

				idx = np.where(pre_y[0] > 0)[0]
				idx = list(idx)

				idx = filter_idx(idx)
				idx = [x for x in idx if if_show[x] == 1]
		else:
				idx = []
				bad_quality_flag = 1

		return idx, ssid, bad_quality_flag

def empty_response():
		symp = ["标签外分类"]
		resp_dict = {"resultcode": 200, "resultmsg": "sucess",
							"idx_code": [],
							"symp_cn": symp,
							"symp_code": [],
							"bad_quality": False,
							"suspected_flag": "",
							"data":{}
							}
		response = json.dumps(resp_dict,
							ensure_ascii=False
					)
		return response

def bad_quality_response():
		symp = ["数据质量差，无法分析"]
		resp_dict = {"resultcode": 200, "resultmsg": "sucess",
							"idx_code": [],
							"symp_cn": symp,
							"symp_code": [],
							"bad_quality": True,
							"suspected_flag": "",
							"data":{}
							}
		response = json.dumps(resp_dict,
							ensure_ascii=False
					)
		return response

def short_response():
		# 判断心电数据是否至少有10秒，否则模型不能识别
		return json.dumps({
				"resultcode": 201,
				"resultmsg": "ecg too short", 
				"data": {},
				"bad_quality": True,
				})

def normal_response(idx, symp_idx_dict, app_key, ssid):
		symp = [symp_idx_dict[x] for x in idx]
		symp = [x.encode('utf-8') for x in symp]
		symp_code = [aha_dict[x] for x in idx]
		print symp_code

		symp_data, status_flag = get_app_dict(symp_code, app_key)

		resp_dict = {
						"resultcode": 200, "resultmsg": "sucess",
						"ssid": ssid,
						"idx_code": idx,
						"symp_cn": symp,
						"symp_code": symp_code,
						"bad_quality": False,
						"data": symp_data,
						"suspected_flag": status_flag
					}
		response = json.dumps(resp_dict,
							ensure_ascii=False
					)
		return response



@app.route("/get_ecg_disease_classification", methods=['post'])
def get_prediction():
	buf = request.data

	req_time = datetime.datetime.now()
	print str(req_time)
	buf = buf.replace("null", "''")
	req_dict = eval(buf)

	#判断是否有心电数据字段
	if 'ecgdata' not in req_dict.keys():
			response = json.dumps({"resultcode": 101, "resultmsg": 'no ecg data', "data":{}})

	elif len(req_dict['ecgdata']) < 5120:
			response = short_response()

	else:	#开始处理数据
			idx, ssid, bad_quality_flag = process_data(req_dict)
			if len(idx) == 0:
				if bad_quality_flag:
					response = bad_quality_response()
				else:
					response = empty_response()
			else:
				response = normal_response(idx, symp_idx_dict, app_key, ssid)
			#update_record(ssid, req_time, request.headers, resp_dict, detect_duration)

			print response
	return response


if __name__ == '__main__':
	#app.run(host='0.0.0.0', threaded=True, debug=False, port=6600)
	app.run('0.0.0.0', debug=True, port=6600, ssl_context='adhoc')





