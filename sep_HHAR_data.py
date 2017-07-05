import os
import sys
import numpy as np 
from copy import deepcopy
from time import gmtime, strftime

from scipy.interpolate import interp1d
from scipy.fftpack import fft


timeLabel = 'Creation_Time'
pairSaveDir = 'Dataset_AccGry_SourceDevice'+'-'+timeLabel+'-avgTime'

mode = 'one_user_out'
select = 'a'

curTime = gmtime()
curRunDir = strftime("%a-%d-%b-%Y-%H_%M_%S+0000", curTime)

# fileIn = open(os.path.join(pairSaveDir, '#DeivceBadData.csv'))
badDevice = ['lgwatch_1', 'lgwatch_2', 's3mini_2']
# for line in fileIn.readlines():
# 	if line[-1] == '\n':
# 		badDevice.append(line[:-1])
# 	else:
# 		badDevice.append(line)

dataList = os.listdir(pairSaveDir)
nameDevList = []
for dataFile in dataList:
	if dataFile[0] == '.':
		continue
	if dataFile[0] == '#':
		continue
	elems = dataFile.split('-')
	curLable = '-'.join(elems[:-1])
	if curLable not in nameDevList:
		nameDevList.append(curLable)
# print nameDevList

sepcturalSamples = 10
fftSpan = 5.
SampSpan = 20.
timeNoiseVar = 0.2
accNoiseVar = 0.5
gyroNoiseVar = 0.2
augNum = 10


dataDict = {}
gtType = ["bike", "sit", "stand", "walk", "stairsup", "stairsdown"]
idxList = range(len(gtType))
gtIdxDict = dict(zip(gtType, idxList))
idxGtDict = dict(zip(idxList, gtType))
wide = 20
wideScaleFactor = 4
labEvery = False
for nameDev in nameDevList:
	for curGt in gtType:
		curType = gtIdxDict[curGt]
		curData_Sep = []
		if os.path.exists(os.path.join(pairSaveDir, nameDev+'-'+curGt)):
			fileIn = open(os.path.join(pairSaveDir, nameDev+'-'+curGt))
			line = fileIn.readline()
			curData = []
			curAccList = []
			curGyroList = []
			curTimeList = []
			lastTime = -1
			startTime = -1
			count = 0
			print nameDev+'-'+curGt
			while len(line) > 0:
				curElem = eval(line)
				curTime = curElem['Time']
				if startTime < 0:
					startTime = curTime
					if startTime < 0:
						print 'Wrong!'
						test = raw_input('continue')
				if abs(curTime - startTime) > fftSpan:
					if len(curAccList) > 0:
						if curTimeList[-1] < fftSpan:
							curAccList.append(deepcopy(curAccList[-1]))
							curGyroList.append(deepcopy(curGyroList[-1]))
							curTimeList.append(fftSpan)
						curAccListOrg = np.array(curAccList).T
						curGyroListOrg = np.array(curGyroList).T
						curTimeListOrg = np.array(curTimeList)

						if mode == 'one_user_out':
							if nameDev[0] == select:
								curAugNum = 1
							else:
								curAugNum = augNum
						elif mode == 'one_model_out':
							if select in nameDev[1:]:
								curAugNum = 1
							else:
								curAugNum = augNum
						else:
							curAugNum = augNum

						for augIdx in xrange(curAugNum):
						# augIdx = 0
							if augIdx == 0:
								curAccList = curAccListOrg + 0.
								curGyroList = curGyroListOrg + 0.
								curTimeList = curTimeListOrg + 0.
							else:
								curAccList = curAccListOrg + np.random.normal(0.,accNoiseVar,curAccListOrg.shape)
								curGyroList = curGyroListOrg + np.random.normal(0.,gyroNoiseVar,curGyroListOrg.shape)
								curTimeList = curTimeListOrg + np.random.normal(0.,timeNoiseVar,curTimeListOrg.shape)

							curTimeList = np.sort(curTimeList)
							if curTimeList[-1] < fftSpan:
								curTimeList[-1] = fftSpan
							if curTimeList[0] > 0.:
								curTimeList[0] = 0.

							accInterp = interp1d(curTimeList, curAccList)
							accInterpTime = np.linspace(0.0, fftSpan*1, sepcturalSamples*1)
							accInterpVal = accInterp(accInterpTime)
							accFFT = fft(accInterpVal).T
							accFFTSamp = accFFT[::1]/float(1)
							accFFTFin = []
							for accFFTElem in accFFTSamp:
								for axisElem in accFFTElem:
									accFFTFin.append(axisElem.real)
									accFFTFin.append(axisElem.imag)

							gyroInterp = interp1d(curTimeList, curGyroList)
							gyroInterpTime = np.linspace(0.0, fftSpan*1, sepcturalSamples*1)
							gyroInterpVal = gyroInterp(gyroInterpTime)
							gyroFFT = fft(gyroInterpVal).T
							gyroFFTSamp = gyroFFT[::1]/float(1)
							# print 'gyroFFTSamp', gyroFFTSamp.shape
							gyroFFTFin = []
							for gyroFFTElem in gyroFFTSamp:
								for axisElem in gyroFFTElem:
									gyroFFTFin.append(axisElem.real)
									gyroFFTFin.append(axisElem.imag)

							curSenData = []
							curSenData += accFFTFin
							curSenData += gyroFFTFin
							
							if len(curData) < augNum:
								curData.append([deepcopy(curSenData)])
							elif startTime - lastTime >= SampSpan and augIdx == 0:
								for curAugData in curData:
									curData_Sep.append(deepcopy(curAugData))
								curData = []
								curData.append([deepcopy(curSenData)])
							else:
								curData[augIdx].append(deepcopy(curSenData))
								
						lastTime = startTime + curTimeList[-1]
						startTime = -1
						curAccList = []
						curGyroList = []
						curTimeList = []
				if startTime < 0:
					startTime = curTime
					if startTime < 0:
						print 'Wrong!'
						test = raw_input('continue')
				if curTime - startTime not in curTimeList:
					curAccList.append(deepcopy(curElem['Accelerometer']))
					curGyroList.append(deepcopy(curElem['Gyroscope']))
					curTimeList.append(curTime - startTime)


				count += 1
				line = fileIn.readline()
		print 'curData_Sep', np.array(curData_Sep).shape
		if not dataDict.has_key(nameDev):
			dataDict[nameDev] = [[],[]]

		for sepData in curData_Sep:
			staIdx = 0
			while staIdx < len(sepData):
				endIdx = min(staIdx + wide, len(sepData))
				if endIdx - staIdx < 5:
				# if endIdx - staIdx < wide:
					break
				dataDict[nameDev][0].append(deepcopy(sepData[staIdx:endIdx]))
				curOut = [0.]*len(gtType)
				curOut[curType] = 1.
				if labEvery:
					curOutPrep = []
					for outIdx in xrange(endIdx - staIdx):
						curOutPrep.append(deepcopy(curOut))
					dataDict[nameDev][1].append(deepcopy(curOutPrep))
				else:
					dataDict[nameDev][1].append(deepcopy(curOut))
				staIdx += int(wide/wideScaleFactor)

X = []
Y = []
maskX = []
evalX = []
evalY = []
evalMaskX = []
paddingVal = 0.
inputFeature = sepcturalSamples*6*2

count = 0
for nameDev in dataDict.keys():
	curX, curY = dataDict[nameDev]
	count += 1
	print '\r', count,
	sys.stdout.flush()
	if mode == 'one_user_out':
		if nameDev[0] == select:
			evalX += deepcopy(curX)
			evalY += deepcopy(curY)
			continue
	elif mode == 'one_model_out':
		if select in nameDev[1:]:
			evalX += deepcopy(curX)
			evalY += deepcopy(curY)
			continue
	X += deepcopy(curX)
	Y += deepcopy(curY)

for idx in xrange(len(X)):
	curLen = len(X[idx])
	maskX.append([[1.0]]*curLen)
	for addIdx in xrange(wide - curLen):
		X[idx].append([paddingVal]*inputFeature)
		maskX[idx].append([0.0])

for idx in xrange(len(evalX)):
	curLen = len(evalX[idx])
	evalMaskX.append([[1.0]]*curLen)
	for addIdx in xrange(wide - curLen):
		evalX[idx].append([paddingVal]*inputFeature)
		evalMaskX[idx].append([0.0])

X = np.array(X)
Y = np.array(Y)
maskX = np.array(maskX)

evalX = np.array(evalX)
evalY = np.array(evalY)
evalMaskX = np.array(evalMaskX)
print 'X', X.shape, X.dtype, 'Y', Y.shape, Y.dtype, 'maskX', maskX.shape, maskX.dtype
print 'evalX', evalX.shape, evalX.dtype, 'evalY', evalY.shape, evalY.dtype, 'evalMaskX', evalMaskX.shape, evalMaskX.dtype

X = np.reshape(X, [-1, wide*inputFeature])
XY = np.hstack((X, Y))
print 'XY', XY.shape
evalX = np.reshape(evalX, [-1, wide*inputFeature])
evalXY = np.hstack((evalX, evalY))
print 'evalXY', evalXY.shape
out_dir = 'sepHARData_'+select
if not os.path.exists(out_dir):
	os.mkdir(out_dir)
	os.mkdir(os.path.join(out_dir, 'train'))
	os.mkdir(os.path.join(out_dir, 'eval'))
idx = 0
for elem in XY:
	fileOut = open(os.path.join(out_dir, 'train', 'train_'+str(idx)+'.csv'), 'w')
	curOut = elem.tolist()
	curOut = [str(ele) for ele in curOut]
	curOut = ','.join(curOut)+'\n'
	fileOut.write(curOut)
	fileOut.close()
	idx += 1
idx = 0
for elem in evalXY:
	fileOut = open(os.path.join(out_dir, 'eval', 'eval_'+str(idx)+'.csv'), 'w')
	curOut = elem.tolist()
	curOut = [str(ele) for ele in curOut]
	curOut = ','.join(curOut)+'\n'
	fileOut.write(curOut)
	fileOut.close()
	idx += 1


