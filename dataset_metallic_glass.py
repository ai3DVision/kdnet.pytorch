from __future__ import print_function
import torch.utils.data as data
from PIL import Image
import os
import os.path
import errno
import torch
import json
import codecs
import numpy as np
#import progressbar
import sys
import torchvision.transforms as transforms
import argparse
import json


class PartDataset(data.Dataset):
    def __init__(self, root, npoints = 2048, classification = False, class_choice = None, train = True):
        self.npoints = npoints
        self.root = root
        self.catfile = os.path.join(self.root, 'synsetoffset2category.txt')
        self.cat = {}

        self.classification = classification

        with open(self.catfile, 'r') as f:
            for line in f:
                ls = line.strip().split()
                #print(ls)
                self.cat[ls[0]] = ls[1]
        #print(self.cat)
        if not class_choice is None:
            self.cat = {k:v for k,v in self.cat.items() if k in class_choice}

        self.meta = {}
        for item in self.cat:
            #print('category', item)
            self.meta[item] = []
            dir_point = os.path.join(self.root, self.cat[item])
            #dir_point = os.path.join(self.root, self.cat[item], 'points')
            #dir_seg = os.path.join(self.root, self.cat[item], 'points_label')
            #print(dir_point, dir_seg)
            fns = sorted(os.listdir(dir_point))
            if train:
                fns = fns[:int(len(fns) * 0.9)]
            else:
                fns = fns[int(len(fns) * 0.9):]

            #print(os.path.basename(fns))
            for fn in fns:
                token = (os.path.splitext(os.path.basename(fn))[0])
                pth = os.path.join(dir_point, token + '.npy')
                self.meta[item].append((pth, pth))

        self.datapath = []
        for item in self.cat:
            for fn in self.meta[item]:
                self.datapath.append((item, fn[0], fn[1]))


        self.classes = dict(zip(self.cat, range(len(self.cat))))
        print(self.classes)
        self.num_seg_classes = 0


    def __getitem__(self, index):
        fn = self.datapath[index]
        cls = self.classes[self.datapath[index][0]]
        cluster_data = np.load(fn[1])
        #print (cluster_data.dtype)
        point_set = cluster_data['delta']
        seg = cluster_data['type_j']
        #print(point_set.shape, seg.shape)


        point_set = point_set - np.expand_dims(np.mean(point_set, axis = 0), 0)
        dist = np.max(np.sqrt(np.sum(point_set ** 2, axis = 1)),0)
        dist = np.expand_dims(np.expand_dims(dist, 0), 1)
        point_set = point_set/dist


        #choice = np.random.choice(len(seg), self.npoints, replace=True)
        #resample
        #point_set = point_set[choice, :]
        #point_set = point_set + 1e-5 * np.random.rand(*point_set.shape)
        #print(point_set.shape)

        #seg = seg[choice]
        point_set = torch.from_numpy(point_set.astype(np.float32))
        seg = torch.from_numpy(seg.astype(np.int64))
        cls = torch.from_numpy(np.array([cls]).astype(np.int64))
        if self.classification:
            return point_set, cls
        else:
            return point_set, seg, cls

    def __len__(self):
        return len(self.datapath)


class PartDatasetSVM(data.Dataset):
    def __init__(self, root, npoints = 2048, classification = False, class_choice = None, train = True):
        self.npoints = npoints
        self.root = root
        self.catfile = os.path.join(self.root, 'synsetoffset2category.txt')
        self.cat = {}

        self.classification = classification

        with open(self.catfile, 'r') as f:
            for line in f:
                ls = line.strip().split()
                #print(ls)
                self.cat[ls[0]] = ls[1]
        #print(self.cat)
        if not class_choice is None:
            self.cat = {k:v for k,v in self.cat.items() if k in class_choice}

        self.meta = {}
        for item in self.cat:
            #print('category', item)
            self.meta[item] = []
            dir_point = os.path.join(self.root, self.cat[item])
            #dir_point = os.path.join(self.root, self.cat[item], 'points')
            #dir_seg = os.path.join(self.root, self.cat[item], 'points_label')
            #print(dir_point, dir_seg)
            fns = sorted(os.listdir(dir_point))
            if train:
                fns = fns[:int(len(fns) * 0.9)]
            else:
                fns = fns[int(len(fns) * 0.9):]

            #print(os.path.basename(fns))
            for fn in fns:
                token = (os.path.splitext(os.path.basename(fn))[0])
                pth = os.path.join(dir_point, token + '.npy')
                self.meta[item].append((pth, pth))

        self.datapath = []
        for item in self.cat:
            for fn in self.meta[item]:
                self.datapath.append((item, fn[0], fn[1]))

        self.classes = dict(zip(self.cat, range(len(self.cat))))
        print(self.classes)
        self.num_seg_classes = 0


    def __getitem__(self, index):
        fn = self.datapath[index]
        cls = self.classes[self.datapath[index][0]]
        cluster_data = np.load(fn[1])
        #print (cluster_data.dtype)
        point_set = cluster_data['delta']
        seg = cluster_data['type_j']
        #print(point_set.shape, seg.shape)

        #point_set = point_set - np.expand_dims(np.mean(point_set, axis = 0), 0)
        dist = np.max(np.sqrt(np.sum(point_set ** 2, axis = 1)),0)
        dist = np.expand_dims(np.expand_dims(dist, 0), 1)
        point_set = point_set/dist
        
        

        dist = np.sum(point_set**2,1)
        bins = np.arange(0,1 + 1e-4,1/30.0)
        feat1 = np.histogram(dist[seg == 1], bins, density = True)[0]
        feat2 = np.histogram(dist[seg == 2], bins, density = True)[0]
        
        feat = np.concatenate([feat1, feat2])
        
        #from IPython import embed; embed()

        #choice = np.random.choice(len(seg), self.npoints, replace=True)
        #resample
        #point_set = point_set[choice, :]
        #point_set = point_set + 1e-5 * np.random.rand(*point_set.shape)
        #print(point_set.shape)

        #seg = seg[choice]
        #point_set = torch.from_numpy(point_set.astype(np.float32))
        #seg = torch.from_numpy(seg.astype(np.int64))
        #cls = torch.from_numpy(np.array([cls]).astype(np.int64))
        
        return feat, cls

    def __len__(self):
        return len(self.datapath)    
    
    
    
if __name__ == '__main__':
    print('test')
    d = PartDataset(root = 'mg', classification = True)
    print(len(d))
    ps, seg = d[0]
    print(ps.size(), ps.type(), seg.size(),seg.type())

    d = PartDatasetSVM(root = 'mg', classification = True)
    print(len(d))
    ps, cls = d[0]
    print(ps.shape, ps.dtype, cls)
