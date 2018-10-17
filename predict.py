#coding=utf-8

import tensorflow as tf
import numpy as np
import os
from sys import argv
#from convert_to_tfrecord import read_and_decode
from xml_parse import parse_ecg_from_xml



def load_graph(path):
	with tf.gfile.FastGFile(path, 'rb') as f:
		graph_def = tf.GraphDef()
		graph_def.ParseFromString(f.read())

		for node in graph_def.node:
			if node.op == 'RefSwitch':
				node.op = 'Switch'
			elif node.op == 'AssignSub':
				node.op = 'Sub'
				# print node.attr.keys()
				if 'use_locking' in node.attr: del node.attr['use_locking']

		tf.import_graph_def(graph_def, name='')
	
	config = tf.ConfigProto(allow_soft_placement=True)
	config.gpu_options.allow_growth = True
	sess = tf.Session(config=config)

	version = sess.graph.get_tensor_by_name("version:0")
	v = sess.run(version, feed_dict={})
	print v

	return sess


def inference(x, sess):
	input_x = sess.graph.get_tensor_by_name("x_ecg:0")
	logit = sess.graph.get_tensor_by_name("logit:0")
	is_train = sess.graph.get_tensor_by_name("is_train:0")
	dropout = sess.graph.get_tensor_by_name("dropout:0")

	pre_y = sess.run(logit, feed_dict={input_x: x, is_train: False, dropout: 0})

	return pre_y



def get_filelist(dir_path):
	filelist = os.listdir(dir_path)
	filelist = [dir_path + '/' + x for x in filelist]

	return filelist


def get_symp_idx_dict(filepath):
		symp_idx_dict = {}
		aha_dict = {}
		ICD_dict = {}
		if_show = {}

		app_key = []

		with open(filepath,'r') as f1:
			txt = f1.readlines()

		for i, line in enumerate(txt):
				l = line.strip().split('\t')
				idx = i
				symp = l[1].strip()
				symp_idx_dict[idx] = symp.decode('utf-8')
				aha_dict[idx] = l[2]
				ICD_dict[idx] = l[3]

				show_cont = int(l[-1])
				if_show[idx] = show_cont 

				if show_cont == 1:
					app_key.append(l[3])
				

		return symp_idx_dict, ICD_dict, if_show, app_key



if __name__ == "__main__":
	pb_filepath = "protobuf/lb_single_lead_2100_TP0.936667_FP0.990000.pb" 
	symp_idx_dict,aha_dict, if_show = get_symp_idx_dict("symp_code.csv")

	sess = load_graph(pb_filepath)


	if True:
		test_x = np.random.random([5120,1])

		pre_y = inference([test_x], sess)
		idx = np.where(pre_y[0] > 0)[0]

		if len(idx) == 0:
				symp == ["标签外分类"]
		else:
				symp = [symp_idx_dict[x] for x in idx]

		print ','.join(symp)

	#output = np.concatenate((np.expand_dims(ID, 1), pre_y), 1)
	#np.savetxt("pred_output.csv", output, delimiter=',', fmt='%f')

	print 'done!'
