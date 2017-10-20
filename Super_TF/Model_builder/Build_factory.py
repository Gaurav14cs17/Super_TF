from utils.builder import Builder
import tensorflow as tf
import os

Segnets = os.path.dirname(os.path.realpath(__file__)) +'\Architecture\Segmentation'
Classnets = os.path.dirname(os.path.realpath(__file__)) +'\Architecture\Classification'

segnet_archs = os.listdir(Segnets)
classnet_archs = os.listdir(Classnets)

for segnet, classnet in zip(segnet_archs, classnet_archs):
    if ".pyc" not in segnet and "__init__" not in segnet and ".py" in segnet:
        exec("from Model_builder.Architecture.Segmentation." + segnet[:-3] + " import *" )

    if ".pyc" not in  classnet and "__init__" not in  classnet and ".py" in  classnet:
        exec("from Model_builder.Architecture.Classification." + classnet[:-3] + " import *" )


class Factory(object):
    """Factory class to build DNN Architectures"""
    #Look into adding a datastructure to keep track of last layer added to the graph

    def get_model(self):

        print('Building ' + self.model_name+'()')
        return (eval('Build_' + self.model_name+'(self.kwargs)'))

    def __init__(self, **kwargs):
        #TODO: WRITE ERROR HANDLER AND PARSER 
        self.model_name = kwargs['Model_name']
        self.summary = kwargs['Summary']
        self.kwargs = kwargs
        #Add more params as required