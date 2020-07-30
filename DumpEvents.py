#!/bin/python
import sys, math, getopt, os, glob, operator
import numpy as np
import numpy.ma as ma 

#from LeftHandSide import lhs, lineno

sys.path.append(r'/opt/mantid/bin')
#sys.path.append(r'/Applications/MantidPlot.app/Contents/MacOS')
import mantid
from mantid.simpleapi import *

def usage():
	print "Options:\n \t--help \n \t--input=INPUTFILE \n \t--output=OUTPUTFILE"
	print "\t --zeroes        This will remove any event where the proton charge is near zero."
	print "\t --filter=89.0   This will only keep events where the proton charge is within 89.0% of the average proton charge "
	print "	Example:"
	print " DumpEvents.py --input=/SNS/REF_M/IPTS-16505/data/REF_M_24240_event.nxs --output=Tof_AbsTime_PixelNo.txt"
	
def main():
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:o:f:z", ["help","input=", "output=", "filter=", "zeroes"])
	except getopt.GetoptError as err:
		# print help information and exit:
		print str(err)  # will print something like "option -a not recognized"
		usage()
		sys.exit(2)
	OutputFile = None
	InputFile = None
	verbose = False
	FilterPercentage = 100.0 # in %
	FilterZeroes = False 

	for o, a in opts:
		if o == "-v"                : verbose = True
		elif o in ("-h", "--help")  : usage(); sys.exit()
		elif o in ("-i", "--input") : InputFile = a
		elif o in ("-o", "--output"): OutputFile = a
		elif o in ("-f", "--filter"): FilterPercentage = a
		elif o in ("-z", "--zeroes"): FilterZeroes = True
		else: assert False, "unhandled option"

	#InputFile='/SNS/REF_M/IPTS-16505/data/REF_M_24240_event.nxs'
	#OutputFile='Tof_AbsTime_PixelNo.txt'
	if InputFile == None:
		usage(); sys.exit()
	else:
		RawEvents=LoadEventNexus(InputFile)
		NoProtonFlash=RemovePromptPulse(RawEvents, Width=300,Frequency=60.0)

		if FilterPercentage < 100.0 : X=FilterBadPulses(NoProtonFlash,LowerCutoff=FilterPercentage) 
		else                        : X=NoProtonFlash
	
		if FilterZeroes == True :  # This will filter out the zero pcharge puleses.  must use the full event filtering
			SplitBoundariesZeroes, infoZeroes  = GenerateEventsFilter(InputWorkspace=X, InformationWorkspace="info",
                                                               Logname="proton_charge", MinimumLogValue=-1, MaximumLogValue=0.1)
			SplitBoundariesNonZeroes, infoNonZeroes  = GenerateEventsFilter(InputWorkspace=X, InformationWorkspace="info",
                                                               Logname="proton_charge", MinimumLogValue=0.1 )

			FilterEvents(InputWorkspace=X, SplitterWorkspace=SplitBoundariesNonZeroes, InformationWorkspace=infoNonZeroes,
                                    OutputWorkspaceBaseName='NonZeroPcData',  GroupWorkspaces=True,
                                    FilterByPulseTime = False, OutputWorkspaceIndexedFrom1 = False,
                                    CorrectionToSample = "None", SpectrumWithoutDetector = "Skip", SplitSampleLogs = False,
                                    OutputTOFCorrectionWorkspace='TOFCorrctedNonZeroePcData')

			# Now that things are split out get the handle to the data we want and set it to our output variable X. 
			NonZeroPcData=mtd['NonZeroPcData']
			X=NonZeroPcData[1]

	if OutputFile == None: OFile = sys.stdout
	else                 : OFile = open(OutputFile, 'w')
	
	OutList =[] ; OutStrings=[]
	for x in range(256*302):
		f=X.getSpectrum(x)
		tofs=f.getTofs(); PulseTimes = f.getPulseTimes()
		for i in range(f.getNumberEvents()): 
			OutList.append((tofs[i], PulseTimes[i], x))	
			OutStrings.append("%s\t%.10f\t%d\n"%(PulseTimes[i], tofs[i], x))	

	OutList.sort(key=operator.itemgetter(1))
	OutStrings.sort()
	
	for item in OutStrings: OFile.write(item)
 
	if OFile is not None: OFile.close()

if __name__ == "__main__":
    main()
