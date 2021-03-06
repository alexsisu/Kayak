# Authors: Harvard Intelligent Probabilistic Systems (HIPS) Group
#          http://hips.seas.harvard.edu
#          Ryan Adams, David Duvenaud, Scott Linderman,
#          Dougal Maclaurin, Jasper Snoek, and others
# Copyright 2014, The President and Fellows of Harvard University
# Distributed under an MIT license. See license.txt file.

import numpy as np
from numpy import exp

import util

from . import Differentiable

class Nonlinearity(Differentiable):
    __slots__ = ['X']
    def __init__(self, X):
        super(Nonlinearity, self).__init__((X,))
        self.X = X

class SoftReLU(Nonlinearity):
    __slots__ = ['scale']
    def __init__(self, X, scale=1.0):
        super(SoftReLU, self).__init__(X)
        self.scale  = scale

    def _compute_value(self):
        # Somewhat complicated to handle overflow.
        X            = self.X.value
        se           = np.seterr(over='ignore')
        exp_X        = np.exp(X / self.scale)
        result       = np.log(1.0 + np.exp( X/self.scale ))*self.scale
        over         = np.isinf(exp_X)
        result[over] = X[over]/self.scale
        return result

    def _local_grad(self, parent, d_out_d_self):
        return d_out_d_self/(1.0 + np.exp( - self.X.value/self.scale ))

class HardReLU(Nonlinearity):
    __slots__ = []
    def __init__(self, X):
        super(HardReLU, self).__init__(X)

    def _compute_value(self):
        return np.maximum(self.X.value, 0.0)

    def _local_grad(self, parent, d_out_d_self):
        return d_out_d_self * (self.X.value > 0)

class TanH(Nonlinearity):
    __slots__ = []
    def __init__(self, X):
        super(TanH, self).__init__(X)

    def _compute_value(self):
        return np.tanh(self.X.value)

    def _local_grad(self, parent, d_out_d_self):
        return d_out_d_self*(1.0 - np.tanh(self.X.value)**2)

class Logistic(Nonlinearity):
    __slots__ = []
    def __init__(self, X):
        super(Logistic, self).__init__(X)

    def _compute_value(self):
        return 1.0/(1.0 + np.exp(-self.X.value))

    def _local_grad(self, parent, d_out_d_self):
        y = self.value
        return d_out_d_self * y * (1.0 - y)

class LogSoftMax(Nonlinearity):
    __slots__ = ['axis']
    def __init__(self, X, axis=1):
        super(LogSoftMax, self).__init__(X)
        self.axis = axis

    def _compute_value(self):
        X = self.X.value
        return X - util.logsumexp(X, axis=self.axis)

    def _local_grad(self, parent, d_out_d_self):
        return d_out_d_self - (np.exp(self.value) * np.sum(d_out_d_self, axis=self.axis, keepdims=True))

class SoftMax(Nonlinearity):
    __slots__ = ['axis']
    def __init__(self, X, axis=1):
        super(SoftMax, self).__init__(X)
        self.axis = axis

    def _compute_value(self):
        X = self.X.value
        return np.exp(X - util.logsumexp(X, axis=self.axis))

    def _local_grad(self, parent, d_out_d_self):
        val = self.value
        return val * (d_out_d_self - np.sum(val * d_out_d_self, axis=self.axis, keepdims=True))

class InputSoftMax(Nonlinearity):
    __slots__ = ['ncolors']
    def __init__(self, X, ncolors=4):
        super(InputSoftMax, self).__init__(X)
        self.ncolors = ncolors
        
    def _compute_value(self):        
        X = self.X.value
        A = np.reshape(X, (X.shape[0], self.ncolors, X.shape[1]//self.ncolors))
        X = A
        return np.exp(X - util.logsumexp(X, axis=1)).reshape((self.X.shape))
    
    def _local_grad(self, parent, d_out_d_self):
        X = self.X.value
        A = np.reshape(X, (X.shape[0], self.ncolors, X.shape[1]//self.ncolors))
        val = self.value.reshape(A.shape)
        d_out_d_self = d_out_d_self.reshape(val.shape)
        return (val * (d_out_d_self - np.sum(val * d_out_d_self, axis=1, keepdims=True))).reshape((self.X.shape[0],-1))
