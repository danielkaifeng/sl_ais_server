#coding=utf-8

def filter_idx(idx):
	#有其它疾病出现，不显示正常心电图
	if 4 in idx and len(idx) > 1:
		idx.remove(4)
	return idx
