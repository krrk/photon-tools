#!/usr/bin/python

import argparse
from argparse import ArgumentParser

import os.path
from photon_tools.favia import corr #photon_tools.favia calls favia from python
from photon_tools import timetag_parse #this extracts timestamps
from photon_tools.pt2_parse import read_pt2

import numpy as np
from matplotlib import pyplot as pl
import math


verbose = False
datapaths = ("/home/sheema/data/new","junk")

def read_timetag(file):
    donor = timetag_parse.get_strobe_events(file,0x1)['t'][1024:] #0x1 is the channel mask
    acceptor = timetag_parse.get_strobe_events(file,0x2)['t'][1024:] #ditto for channel 2
    return (1./128e6, donor, acceptor)
    
def read_data(file):
    if file.name.endswith('.timetag'):
        return read_timetag(file)
    elif file.name.endswith('.pt2'):
        a = read_pt2(file.name, 0)
        b = read_pt2(file.name, 1)
        return (1e-12, a, b)
    else:
        raise RuntimeError("Unknown file type")

def correlate_timetags(file):
    jiffy,donor,acceptor = read_data(file)

    fname = os.path.basename(file.name)
    print 'Read %s: %d acceptor events, %d donor events' % (fname, len(acceptor), len(donor))
    dcorr = corr(donor, donor, jiffy=jiffy, short_grain=1e-7, verbose=verbose)
    acorr = corr(acceptor ,acceptor, jiffy=jiffy, short_grain=1e-7, verbose=verbose)
    xcorr = corr(donor, acceptor, jiffy=jiffy, short_grain=1e-7, verbose=verbose)
    np.savetxt(fname+'.dcorr', dcorr)
    np.savetxt(fname+'.acorr', acorr)
    np.savetxt(fname+'.xcorr', xcorr)
    plot_corr(dcorr, fname+'.dcorr.png')
    plot_corr(acorr, fname+'.acorr.png')
    plot_corr(xcorr, fname+'.xcorr.png')
    
    #Note that files have the following columns:  
    #time, logtime, dot, correlation function, uncertainty, mean, uncertainty in mean.

def plot_corr(corr, output=None):
    pl.clf()
    pl.xscale('log')
    pl.errorbar(corr['lag'], corr['dotnormed'], yerr=corr['bar'], fmt='.')
    pl.xlabel('Lag (s)')
    pl.ylabel('Correlation function')
    if output is not None:
	pl.savefig(output)
    
parser = ArgumentParser(description='Compute and plot correlation functions of photon timestamps')
parser.add_argument('files', metavar='FILES', type=argparse.FileType('r'), nargs='+',
		     help='Input files in either PT2 or FPGA timetagger format')
args = parser.parse_args()

for file in args.files:
    correlate_timetags(file)
    