import time
import datetime
import pymongo

client = pymongo.MongoClient('127.0.0.1', 10000)
db = client.get_database('sl_ais_prediction')
request_log = db.get_collection('sl_request_log')

def update_record(ecgdataid, req_time, request_headers, resp_dict, detect_duration):
	#ecg_filter.update({'_id':record['_id']},{'$set':{'ecgdataid':str(record['ecgdataid'])}},multi=True)
	request_log.insert({
					"ecgdataid": ecgdataid, 
					"prediction": resp_dict, 
					"request_headers": dict(request_headers), 
					"request_time": req_time, 
					"respone_time": datetime.datetime.now(), 
					"detect_duration": detect_duration
					}
				)

