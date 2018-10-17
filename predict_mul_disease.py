# -*- coding: utf-8 -*-
"""
Created on Mon, 2017-11-13
@author: daniel deng  

Mul-disease recognization for ECG time series data using dense prediction.
1. 支持不定长输入
2. 支持批量预测或单条预测

用法:
python predict_mul_disease.py test_x.csv v2.acc0.800039.pb
[1, 14, 2,  7] 正常, 噪音, 房颤, 右束支
"""


import tensorflow as tf
import numpy as np
import os
from sys import argv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def normalization(seq):
		new_data = []
		epilson = 1e-8

		x_max = max(seq)
		x_min = min(seq)
		new_seq = [(x - x_min + epilson) / (x_max - x_min + epilson) for x in seq]
		
		return np.array(new_seq)



def load_graph2(path="protobuf/fcn_v1.0.3.pb"):
	with tf.gfile.FastGFile(path, 'rb') as f:
		graph_def = tf.GraphDef()
		tf.reset_default_graph()
		graph_def.ParseFromString(f.read())

		for node in graph_def.node:
			if node.op == 'RefSwitch':
				node.op = 'Switch'
			elif node.op == 'AssignSub':
				node.op = 'Sub'
				if 'use_locking' in node.attr: del node.attr['use_locking']

		tf.import_graph_def(graph_def, name='')

	sess = tf.Session()

	version = sess.graph.get_tensor_by_name("version:0")
	v = sess.run(version)
	
	return sess,v


def inference2(sess, x):
	#from train.py:
	#	output_node_names=["x", 'dropout',  'features','is_train','version','batchs', 'class', 'input_length']
	print x.shape


	input_x = sess.graph.get_tensor_by_name("x:0")
	disease_class = sess.graph.get_tensor_by_name("class:0")
	is_train = sess.graph.get_tensor_by_name("is_train:0")
	n_input = sess.graph.get_tensor_by_name("input_length:0")
	dropout = sess.graph.get_tensor_by_name("dropout:0")
	batch = sess.graph.get_tensor_by_name("batchs:0")
	dis_class = sess.run(disease_class, feed_dict={input_x: x, is_train: False, dropout: 0, n_input: x.shape[1], batch: x.shape[0]})
	return dis_class


## 这个函数不调用
def get_clean_ecg(x, feature_class):
	threshold = 2  # 判定为正常信号的阈值, > 0为噪音
	step = 30
	seed = []
	clean_ecg = []

	nnn = []
	for n in range(0,len(x)-step,step):
		num_noise = len([i for i in range(step) if feature_class[n+i] == 1]) 
		seq_x = x[n:n+step]

		nnn.append(num_noise)
		if num_noise < threshold and np.mean(seq_x) < 2000:
				seed += list(seq_x)
		elif len(seed) >= 512 * 10:	
				#print np.mean(seq_x)
				#seed = seed + [-1]*(len(x) - len(seed))  #是否补数成定长序列
				clean_ecg.append(seed)
				seed = []
		else:
				seed = []

	if len(seed) >= 512 * 10:	# 每条有效信号大于10秒才保存
			print np.mean(seq_x)
			clean_ecg.append(seed)

	print "num of noise:\n", nnn

	return clean_ecg


if __name__ == "__main__":
		sess, version = load_graph2()
		print "noise algorithm version: " + version

		for iii in range(10):
				# 输入的test_x为归一化到0-1的数据
				#test_x = np.loadtxt(x_file_path, delimiter=',')[:5]
				test_x = np.random.random(10240*4)

				disease_class = inference2(sess, np.array([test_x]))
				print disease_class
				print np.unique(disease_class)

				clean_ecg = get_clean_ecg(test_x, disease_class[0])
				for seq in clean_ecg:
						print len(seq)


		#visual(test_x, disease_class, "mul_disease_%s" % version)
		print '\n'.join([str(x) + ':' + y for x,y in zip([0, 1, 2, 3],["正常","噪音", "房颤", "右束支"])])
		print 'done'


		"""
		output = [] 
		for i in range(test_x.shape[0]):
			clean_ecg = get_clean_ecg(test_x[i], feature_class[i], f_thres[i])
			if len(clean_ecg) == 0:
					continue
			else:
				output += clean_ecg

		"""

