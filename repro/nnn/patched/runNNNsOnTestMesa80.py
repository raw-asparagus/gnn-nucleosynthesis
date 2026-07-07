# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 12:12:52 2024

@author: aldana
"""

from NNNfunctionsCompPlusEps import *
#import pandas as pd
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import os
#import shutil
import statistics

c_light = 3*10**10 #cgs  # PATCH: used below but undefined in the shipped script; value as in their plotDensityMaps.py


def listOutputFiles(testDataDir):  # PATCH: deterministic order; skip non-bbq files (desktop.ini etc.)
    return [f for f in sorted(os.listdir(testDataDir)) if f.startswith('output')]


def parseLogRho(bbqFileName):  # PATCH: shipped test files end '..._rho_<val>.txt' (no _Ye_ suffix)
    return float(bbqFileName.split('_')[4].removesuffix('.txt'))


def findIsoParams(mesaDir,database_file_path,isotopesNum, _cache={}):
    # PATCH: memoized — upstream re-reads a ~150 MB csv inside the per-test-file
    # loop (685x per run); the returned arrays are identical every call.
    _key = (mesaDir, database_file_path, isotopesNum)
    if _key in _cache:
        return _cache[_key]

    database = pd.read_csv(database_file_path)

    
    database.drop(columns = ['Age'], inplace = True)

    if 'Ye' in database.columns:
        database.drop(columns = ['Ye'], inplace=True)

    # isotopeNames = np.array([column.split('_')[1] for column in database.columns[2:2+isotopesNum]])
    isotopeNames = np.array([column.split('_')[1] for column in database.columns[2:2+isotopesNum]])

    with open(mesaDir + '/data/chem_data/isotopes.data') as f:
        allIsotopesData = f.readlines()

    allIsotopesAZYeM = {}
    for i in range(1, len(allIsotopesData), 4):
        currentLine = allIsotopesData[i].split()
        isotopeName = currentLine[0]
        isotopeM = float(currentLine[1])
        isotopeZ = int(currentLine[2])
        isotopeN = int(currentLine[3])
        isotopeA = isotopeZ + isotopeN
        isotopeYe = isotopeZ / isotopeA
        allIsotopesAZYeM[isotopeName] = np.array([isotopeA, isotopeZ, isotopeYe, isotopeM])


    isotopesN = []
    isotopesYe = []
    isotopesA = []
    isotopesZ = []
    isotopesM = []


    for isotope in isotopeNames:
        isotopesA.append(int(allIsotopesAZYeM[isotope][0]))
        isotopesZ.append(int(allIsotopesAZYeM[isotope][1]))
        isotopesYe.append(allIsotopesAZYeM[isotope][2])
        isotopesM.append(allIsotopesAZYeM[isotope][3])
        isotopesN.append(int(allIsotopesAZYeM[isotope][0] - allIsotopesAZYeM[isotope][1]))

    isotopesYe = np.array(isotopesYe)
    isotopesA = np.array(isotopesA)
    isotopesZ = np.array(isotopesZ)
    isotopesM = np.array(isotopesM)
    isotopesM = isotopesM*(1.67*10**(-24)) #covert from amu to grams

    _cache[_key] = (isotopesYe, isotopesA, isotopesZ, isotopesM)  # PATCH
    return isotopesYe, isotopesA, isotopesZ, isotopesM

def findBbqParams(testDataDir,timeStepIndex,initialAgeIndex,finalAgeIndex,mesaDir,database_file_path,isotopesNum):
        
    allLogT = []
    allLogRho = []
    
    allbbqComps = []
    bbqYe = []
    bbqAbar = []
    bbqZbar = []
    
    allbbqEpsNuc = []
    allbbqEpsNu = []

    
    isotopesYe, isotopesA, isotopesZ, isotopesM = findIsoParams(mesaDir,database_file_path,isotopesNum)
    
    
    files_count = 0

    for bbqFileName in listOutputFiles(testDataDir):  # PATCH
        with open(testDataDir + bbqFileName) as f:
            currentData = f.readlines()
        if len(currentData) == 1003: #103 for shorter times
            initialComp = [float(isotopeAbundance) for isotopeAbundance in currentData[initialAgeIndex].split()[4:]]
            logT = float(bbqFileName.split('_')[2])
            logRho = parseLogRho(bbqFileName)  # PATCH
            timeStep = float(currentData[timeStepIndex].split()[0])
            ageInitial = float(currentData[initialAgeIndex].split()[0])
            ageFinal = float(currentData[finalAgeIndex].split()[0])
            timeStepsNum = round((ageFinal - ageInitial) / timeStep) # Make sure all files have the same ageFinal !!



            allLogT.append(logT)
            allLogRho.append(logRho)
    
            
            bbqCompsSingleFile = []
            bbqYeSingleFile = []
            bbqAbarSingleFile = []
            bbqZbarSingleFile = []
            ageSingleFile = []
            timeStepsNumSingleFile = []
            
            bbqEpsNucSingleFile = []
            bbqEpsNuSingleFile = []

            
    
            bbqFinalCompSingleFile = [float(isotopeAbundance) if float(isotopeAbundance)>1e-15 else 1e-15 for isotopeAbundance in currentData[finalAgeIndex].split()[4:]]
            for i in range(initialAgeIndex,finalAgeIndex):    
                bbqCompsSingleFile.append([float(isotopeAbundance) if float(isotopeAbundance)>1e-15 else 1e-15 for isotopeAbundance in currentData[i].split()[4:]])
                #bbqYeSingleFile.append(np.sum(np.array(bbqCompsSingleFile[i]) * isotopesYe))
                bbqEpsNucSingleFile.append(float(currentData[i].split()[2]))
                bbqEpsNuSingleFile.append(float(currentData[i].split()[3]))

            
            for i in range(len(bbqCompsSingleFile)):
                bbqYeSingleFile.append(np.sum(np.array(bbqCompsSingleFile[i]) * isotopesYe))
                bbqAbarSingleFile.append(np.sum(bbqCompsSingleFile[i] * isotopesA))
                bbqZbarSingleFile.append(np.sum(bbqCompsSingleFile[i] * isotopesZ))
    
            
            allbbqComps.append(bbqCompsSingleFile)
            bbqYe.append(bbqYeSingleFile)
            bbqAbar.append(bbqAbarSingleFile)  
            bbqZbar.append(bbqZbarSingleFile)
            
            allbbqEpsNuc.append(bbqEpsNucSingleFile)
            allbbqEpsNu.append(bbqEpsNuSingleFile)

            
            files_count+=1
        
            print('Iterating over file number:',files_count)
        
        else:
            print(bbqFileName,'is bad!')
            
    print('timeStepsNum',timeStepsNum)

            
    bbqParams = {'allbbqComps':allbbqComps,'bbqYe':bbqYe, 'bbqAbar':bbqAbar, 'bbqZbar':bbqZbar,'allLogT':allLogT,
                 'allLogRho':allLogRho,'allbbqEpsNuc':allbbqEpsNuc,'allbbqEpsNu':allbbqEpsNu}

    return bbqParams

def predictNNNcompsMultipleSteps(baseDir,testDataDir,trainedModelBaseDir,trainedModel,mesaDir,database_file_path,timeStepIndex,initialAgeIndex,finalAgeIndex,isotopesNum):
    
    
    torch.set_float32_matmul_precision('medium')
    
    trainingDatasetSize = int(float(trainedModel.split('_')[3]))
    layersNum = int(trainedModel.split('_')[6])
    neuronsNumFactor = int(trainedModel.split('_')[8])

    # PATCH: dropped unused `data = DataModule(trainingDatasetSize); data.setup('')`
    # (loads the multi-GB training CSV and is never referenced afterwards)

    checkpointsDirName = trainedModelBaseDir + trainedModel + '/checkpoints/'
    fileNames = [file for file in os.listdir(checkpointsDirName) if file.endswith('.ckpt')]  # PATCH: skip desktop.ini too
    
    model = nuclearNN.load_from_checkpoint(checkpointsDirName + fileNames[0], layersNum = layersNum, neuronsNumFactor = neuronsNumFactor,map_location=torch.device("cpu")).to('cpu')
        
    allNNNcomps = []
    nnnYe = [] 
    nnnAbar = []
    nnnZbar = []
    nnnQ = []
    
    allNNNeps = []



    files_count = 0

    for bbqFileName in listOutputFiles(testDataDir):  # PATCH
        with open(testDataDir + bbqFileName) as f:
            currentData = f.readlines()
        if len(currentData) == 1003: # 103 for shorter times
            initialComp = [float(isotopeAbundance) for isotopeAbundance in currentData[initialAgeIndex].split()[4:]]
            logT = float(bbqFileName.split('_')[2])
            logRho = parseLogRho(bbqFileName)  # PATCH
            timeStep = float(currentData[timeStepIndex].split()[0])
            ageInitial = float(currentData[initialAgeIndex].split()[0])
            ageFinal = float(currentData[finalAgeIndex].split()[0])
            timeStepsNum = round((ageFinal - ageInitial) / timeStep) # Make sure all files have the same ageFinal !!
     
        nnnInput = torch.tensor([[logT, logRho] + initialComp])
        TandRho = nnnInput[:, 0:2]
        
        allNNNcompsSingleFile = [] # Will contain all compositions predice by NNN every time we run NNN on itself, for one bbq output file
        nnnYeSingleFile = [] 
        nnnAbarSingleFile = []
        nnnZbarSingleFile = []
        nnnQsingleFile = []
        
        allNNNepsSingleFile = [] # Will contain all compositions predice by NNN every time we run NNN on itself, for one bbq output file

        # allNNNcompsSingleFile.append(torch.exp(model(nnnInput))) # we run the NNN on bbq composition 

        output = model(nnnInput)  # Get model predictions
        
        # Separate the first 80 and the last 2 outputs
        first_80_outputs = output[:, 0:isotopesNum]  # First 80 outputs
        last_2_outputs = output[:, isotopesNum:]   # Last 2 outputs
        
        # print("first_80_outputs shape:", first_80_outputs.shape)
        # print("last_2_outputs shape:", last_2_outputs.shape)

        
        # Apply exp to the first 80 outputs (reverse log_softmax)
        first_80_exp = torch.exp(first_80_outputs)
        
        # Append to respective lists
        allNNNcompsSingleFile.append(first_80_exp)  # Store the first 80 outputs
        allNNNepsSingleFile.append(last_2_outputs)  # Store the last 2 outputs


        for i in range(timeStepsNum):
            nextStepOutput = model(torch.cat((TandRho, allNNNcompsSingleFile[i]), dim = 1))
            allNNNcompsSingleFile.append(torch.exp(nextStepOutput[:, 0:isotopesNum])) #we run the NNN on its own output
            allNNNepsSingleFile.append(nextStepOutput[:, isotopesNum:])
        
        isotopesYe, isotopesA, isotopesZ, isotopesM = findIsoParams(mesaDir,database_file_path,isotopesNum)
        
        # print("isotopesYe:", len(isotopesYe))

        
        for i in range(len(allNNNcompsSingleFile)):
            allNNNcompsSingleFile[i] = allNNNcompsSingleFile[i][0, :].detach().numpy()
            nnnYeSingleFile.append(np.sum(np.array(allNNNcompsSingleFile[i]) * isotopesYe))
            nnnAbarSingleFile.append(np.sum(np.array(allNNNcompsSingleFile[i]) * isotopesA))
            nnnZbarSingleFile.append(np.sum(np.array(allNNNcompsSingleFile[i]) * isotopesZ))
            nnnQsingleFile.append((c_light**2)*(np.sum(allNNNcompsSingleFile[i] * isotopesM)-np.sum(initialComp * isotopesM)))
            
            allNNNepsSingleFile[i] = (10**16)*allNNNepsSingleFile[i][0, :].detach().numpy() #  we divided by 10^16 in the database 
                                                                                            # file so it would be eassier to train

            
            
        allNNNcomps.append(allNNNcompsSingleFile)
        nnnYe.append(nnnYeSingleFile)
        nnnAbar.append(nnnAbarSingleFile)
        nnnZbar.append(nnnZbarSingleFile)
        nnnQ.append(nnnQsingleFile)
        
        allNNNeps.append(allNNNepsSingleFile)
        NNNepsNuc = [item[0][0] for item in allNNNeps]
        NNNepsNu = [item[0][1] for item in allNNNeps]
        
        #print('NNNepsNuc',NNNepsNuc)
        #print('NNNepsNu',NNNepsNu)

        # NNNepsNu = [x / 10**3 for x in NNNepsNu]  # For dt=10,100,1000, we normalized eps_nuc by 10^16 but eps_nu by 10**13

        #print('NNNepsNuc After Multiplying',NNNepsNuc)
        #print('NNNepsNu After Multiplying',NNNepsNu)

        
        files_count+=1
        
            
        print('Iterating over file number:',files_count)
            
    else:
        
        print(bbqFileName,'is bad!')


    allNNNcompsToSave = np.stack(allNNNcomps)

    
    filename = baseDir + '/Results/Files/NNNparams.csv'
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["allNNNcomps", "nnnYe", "nnnAbar", "nnnZbar", "nnnQ", "allNNNeps", "NNNepsNuc", "NNNepsNu"])  # Writing header
        for nnn_comps, nnn_Ye, nnn_Abar, nnn_Zbar, nnn_Q, nnn_eps, nnn_eps_nuc, nnn_eps_nu in zip(allNNNcomps, nnnYe, nnnAbar, nnnZbar, nnnQ, allNNNeps, NNNepsNuc, NNNepsNu):
            writer.writerow([nnn_comps, nnn_Ye, nnn_Abar, nnn_Zbar, nnn_Q, nnn_eps, nnn_eps_nuc, nnn_eps_nu])
            
    nnnParams = {'allNNNcomps':allNNNcomps,'nnnYe':nnnYe, 'nnnAbar':nnnAbar, 'nnnZbar':nnnZbar, 'nnnQ':nnnQ, 
                 'allNNNeps':allNNNeps,'NNNepsNuc':NNNepsNuc,'NNNepsNu':NNNepsNuc}

    filename = baseDir + '/Results/Files/NNNcomps'
    np.savez(filename, allNNNcompsToSave = allNNNcompsToSave)
       

    return nnnParams


def computeNNNlosses(baseDir,testDataDir,initialAgeIndex,finalAgeIndex,bbqParamsMesa80,nnnParams):
    #finaAgeIndexArray = np.arange(finalAgeIndex, finalAgeIndex + 30, 5) # Good for 10000 timesteps
    #finaAgeIndexArray = np.arange(finalAgeIndex, finalAgeIndex + 7, 1) # Good for 100 timesteps
    #finaAgeIndexArray = np.arange(finalAgeIndex, finalAgeIndex + 18, 3) # Good for 1000 timesteps

    #finaAgeIndexArray = np.array([70,72,74])

    finaAgeIndexArray = np.arange(initialAgeIndex+1, finalAgeIndex+1, 1)
    ageFinalList = []
    timeStepsNumList = []

    bbqFileName = listOutputFiles(testDataDir)[0]  # PATCH

    with open(testDataDir + bbqFileName) as f:
        currentData = f.readlines()
    if len(currentData) == 1003: #103 for shorter times
        timeStep = float(currentData[timeStepIndex].split()[0])
        ageInitial = float(currentData[initialAgeIndex].split()[0])
        for i in range(len(finaAgeIndexArray)):
            ageFinalList.append(float(currentData[finaAgeIndexArray[i]].split()[0]))
            timeStepsNumList.append(round((ageFinalList[i] - ageInitial) / timeStep))
    else:
        print(bbqFileName,'is bad!')


    timeStepsNumArray = np.array(timeStepsNumList)       
    timeStepsNumArray = timeStepsNumArray.astype(int)
        
    
    allbbqComps = np.array(bbqParamsMesa80["allbbqComps"])
    bbqYe = np.array(bbqParamsMesa80["bbqYe"])
    bbqAbar = np.array(bbqParamsMesa80["bbqAbar"])
    bbqZbar = np.array(bbqParamsMesa80["bbqZbar"])

    allbbqEpsNuc = np.array(bbqParamsMesa80["allbbqEpsNuc"])
    allbbqEpsNu = np.array(bbqParamsMesa80["allbbqEpsNu"])

    
    allNNNcomps = np.array(nnnParams["allNNNcomps"])
    nnnYe = np.array(nnnParams["nnnYe"])
    nnnAbar = np.array(nnnParams["nnnAbar"])
    nnnZbar = np.array(nnnParams["nnnZbar"])
    nnnQ = np.array(nnnParams["nnnQ"])
    
    NNNepsNuc = np.array(nnnParams["NNNepsNuc"])
    NNNepsNu = np.array(nnnParams["NNNepsNu"])
    
    
    LinearLoss = []
    YeLoss = []
    AbarLoss = []
    ZbarLoss = []
    Qloss = []
    YeLossNoAbs = []
    
    epsNucLoss = []
    epsNuLoss = []
    epsNucLossNoAbs = []
    epsNuLossNoAbs = []



    for i in range(len(allNNNcomps)):
        #print("Shape of allbbqComps[i]:", np.array(allbbqComps[i]).shape)
        #print("Shape of allNNNcomps[i]:", np.array(allNNNcomps[i]).shape)
        #print("TimeStepsNumArray:", timeStepsNumArray)
        LinearLoss.append(np.sum(np.abs(allbbqComps[i]-np.array(allNNNcomps[i])[timeStepsNumArray]),axis = 1)) # axis = 1 to sum over the rows of the matrix rather than columns (default)
        YeLoss.append(np.abs(bbqYe[i]-np.array(nnnYe[i])[timeStepsNumArray]))
        AbarLoss.append(np.abs(bbqAbar[i]-np.array(nnnAbar[i])[timeStepsNumArray]))
        ZbarLoss.append(np.abs(bbqZbar[i]-np.array(nnnZbar[i])[timeStepsNumArray]))
        YeLossNoAbs.append(bbqYe[i]-np.array(nnnYe[i])[timeStepsNumArray])
        
        epsNucLoss.append(np.abs(allbbqEpsNuc[i][-1]-np.array(NNNepsNuc[i])))
        epsNuLoss.append(np.abs(allbbqEpsNu[i][-1]-np.array(NNNepsNu[i])))
        epsNucLossNoAbs.append(allbbqEpsNuc[i][-1]-np.array(NNNepsNuc[i]))
        epsNuLossNoAbs.append(allbbqEpsNu[i][-1]-np.array(NNNepsNu[i]))


    
    epsNucLoss = [values if isinstance(values, (list, np.ndarray)) else [values] for values in epsNucLoss]
    epsNuLoss = [values if isinstance(values, (list, np.ndarray)) else [values] for values in epsNuLoss]
    epsNucLossNoAbs = [values if isinstance(values, (list, np.ndarray)) else [values] for values in epsNucLossNoAbs]
    epsNuLossNoAbs = [values if isinstance(values, (list, np.ndarray)) else [values] for values in epsNuLossNoAbs]


    AverageLinearLoss = [sum(values) / len(values) for values in zip(*LinearLoss)]
    AverageYeLoss = [sum(values) / len(values) for values in zip(*YeLoss)]
    AverageAbarLoss = [sum(values) / len(values) for values in zip(*AbarLoss)]
    AverageZbarLoss = [sum(values) / len(values) for values in zip(*ZbarLoss)]
    AverageQloss = [sum(values) / len(values) for values in zip(*Qloss)]
    AverageYeLossNoAbs = [sum(values) / len(values) for values in zip(*YeLossNoAbs)]
    
    AverageEpsNucLoss = [sum(values) / len(values) for values in zip(*epsNucLoss)]
    AverageEpsNuLoss = [sum(values) / len(values) for values in zip(*epsNuLoss)]
    AverageEpsNucLossNoAbs = [sum(values) / len(values) for values in zip(*epsNucLossNoAbs)]
    AverageEpsNuLossNoAbs = [sum(values) / len(values) for values in zip(*epsNuLossNoAbs)]

        
    MedianLinearLoss = [statistics.median(values) for values in zip(*LinearLoss)]
    MedianYeLoss = [statistics.median(values) for values in zip(*YeLoss)]    
    MedianEpsNucLoss = [statistics.median(values) for values in zip(*epsNucLoss)]
    MedianEpsNuLoss = [statistics.median(values) for values in zip(*epsNuLoss)]




    filename = baseDir + '/Results/Files/AverageLossesNNN.csv'
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["AverageLinearLoss", "AverageYeLoss","AverageAbarLoss", "AverageZbarLoss","Timesteps",
                         "AverageYeLossNoAbs","AverageEpsNucLoss", "AverageEpsNuLoss","AverageEpsNucLossNoAbs",
                         "AverageEpsNuLossNoAbs",
                         "MedianLinearLoss","MedianYeLoss","MedianEpsNucLoss","MedianEpsNuLoss"])  # Writing header
        for linear_loss, ye_loss, Abar_loss, Zbar_loss, timestep, ye_loss_no_abs, eps_nuc_loss, eps_nu_loss, eps_nuc_loss_no_abs, eps_nu_loss_no_abs,linear_loss_m, ye_loss_m, eps_nuc_loss_m, eps_nu_loss_m in zip(AverageLinearLoss, AverageYeLoss, AverageAbarLoss, AverageZbarLoss, timeStepsNumArray,AverageYeLossNoAbs,AverageEpsNucLoss,AverageEpsNuLoss,AverageEpsNucLossNoAbs,AverageEpsNuLossNoAbs,MedianLinearLoss,MedianYeLoss,MedianEpsNucLoss,MedianEpsNuLoss):
            writer.writerow([linear_loss, ye_loss, Abar_loss,  Zbar_loss, timestep,ye_loss_no_abs,eps_nuc_loss, eps_nu_loss, eps_nuc_loss_no_abs, eps_nu_loss_no_abs,linear_loss_m, ye_loss_m, eps_nuc_loss_m, eps_nu_loss_m])


    bbqAverageYe = [sum(values) / len(values) for values in zip(*bbqYe)]
    nnnAverageYe = [sum(values) / len(values) for values in zip(*nnnYe)]
    bbqAverageAbar = [sum(values) / len(values) for values in zip(*bbqAbar)]
    nnnAverageAbar = [sum(values) / len(values) for values in zip(*nnnAbar)]
    bbqAverageZbar = [sum(values) / len(values) for values in zip(*bbqZbar)]
    nnnAverageZbar = [sum(values) / len(values) for values in zip(*nnnZbar)]
    
    bbqAverageEpsNuc = [sum(values) / len(values) for values in zip(*allbbqEpsNuc)]
    bbqAverageEpsNu = [sum(values) / len(values) for values in zip(*allbbqEpsNu)]
    NNNepsNuc = [values if isinstance(values, (list, np.ndarray)) else [values] for values in NNNepsNuc]
    nnnAverageEpsNuc = [sum(values) / len(values) for values in zip(*NNNepsNuc)] 
    NNNepsNu = [values if isinstance(values, (list, np.ndarray)) else [values] for values in NNNepsNu]
    nnnAverageEpsNu = [sum(values) / len(values) for values in zip(*NNNepsNu)]
    
    
    bbqMedianYe = [statistics.median(values) for values in zip(*bbqYe)]
    nnnMedianYe = [statistics.median(values) for values in zip(*nnnYe)]
    bbqMedianEpsNuc = [statistics.median(values) for values in zip(*allbbqEpsNuc)]
    bbqMedianEpsNu = [statistics.median(values) for values in zip(*allbbqEpsNu)]
    nnnMedianEpsNuc =  [statistics.median(values) for values in zip(*NNNepsNuc)]
    nnnMedianEpsNu =  [statistics.median(values) for values in zip(*NNNepsNu)]


    filename = baseDir + '/Results/Files/AverageParamNNN.csv'
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["bbqAverageYe", "nnnAverageYe", "bbqAverageAbar", "nnnAverageAbar","bbqAverageZbar", "nnnAverageZbar",
                         "Timesteps","bbqAverageEpsNuc", "nnnAverageEpsNuc", "bbqAverageEpsNu", 
                         "nnnAverageEpsNu",
                         "bbqMedianYe","nnnMedianYe","bbqMedianEpsNuc","bbqMedianEpsNu","nnnMedianEpsNuc","nnnMedianEpsNu"])  # Writing header
        for Ye_bbq, Ye_nnn, A_bar_bbq, A_bar_nnn, Z_bar_bbq, Z_bar_nnn, timestep, eps_nuc_bbq, eps_nuc_nnn, eps_nu_bbq, eps_nu_nnn,Ye_bbq_m, Ye_nnn_m, eps_nuc_bbq_m, eps_nu_bbq_m, eps_nuc_nnn_m, eps_nu_nnn_m in zip(bbqAverageYe,nnnAverageYe, bbqAverageAbar, nnnAverageAbar, bbqAverageZbar, nnnAverageZbar,timeStepsNumArray,bbqAverageEpsNuc,nnnAverageEpsNuc, bbqAverageEpsNu, nnnAverageEpsNu,bbqMedianYe,nnnMedianYe,bbqMedianEpsNuc,bbqMedianEpsNu,nnnMedianEpsNuc,nnnMedianEpsNu):
            writer.writerow([Ye_bbq, Ye_nnn, A_bar_bbq, A_bar_nnn, Z_bar_bbq, Z_bar_nnn,timestep, eps_nuc_bbq, eps_nuc_nnn, eps_nu_bbq, eps_nu_nnn,Ye_bbq_m, Ye_nnn_m, eps_nuc_bbq_m, eps_nu_bbq_m, eps_nuc_nnn_m, eps_nu_nnn_m])


    
    LossesAndParams = {'bbqAverageYe':bbqAverageYe,'nnnAverageYe':nnnAverageYe, 'bbqAverageAbar':bbqAverageAbar, 
                       'nnnAverageAbar':nnnAverageAbar,'bbqAverageZbar':bbqAverageZbar, 'nnnAverageZbar':nnnAverageZbar,
                       'Timesteps':timeStepsNumArray,
                       'bbqAverageEpsNuc':bbqAverageEpsNuc,'nnnAverageEpsNuc':nnnAverageEpsNuc, 'bbqAverageEpsNu':bbqAverageEpsNu,
                       'nnnAverageEpsNu':nnnAverageEpsNu}

    return LossesAndParams



# %% Run NNN on test data

# Dont forget to check eps normzliation in allNNNepsSingleFile. You need to re-multiply by the number you divided the training sets. 


start_time = time.time()

# PATCH: whole driver block parameterized via environment variables; upstream
# logic (index mapping, call sequence, arguments) preserved verbatim.
mesaDir = os.environ['NNN_MESA_DIR']            # dir containing data/chem_data/isotopes.data
zenodoDir = os.environ['NNN_ZENODO_DIR']        # .../data/zenodo/NuclearNeuralNetworks
resultsDir = os.environ['NNN_RESULTS_DIR']      # per-run output dir; CSVs land in <resultsDir>/Results/Files/
netName = os.environ['NNN_NET']                 # 'mesa_80' | 'mesa_151'
dtLabel = os.environ['NNN_DT']                  # '1e-6' ... '1e2'
layersNumForNet = {'mesa_80': 12, 'mesa_151': 9}[netName]
isotopesNumForNet = {'mesa_80': 80, 'mesa_151': 151}[netName]
baseDir = resultsDir

# The index of the age on which we trained the NNNs
# For 1001 timesteps from -10 to 2 [1e-6: 134, 1e-5: 184, 1e-4: 234, 1e-3: 284; 1e-2: 334; 1e-1: 384, 1e0: 434, 1e1: 484, 1e2: 534]
timeStepIndexByDt = {'1e-6': 134, '1e-5': 184, '1e-4': 234, '1e-3': 284, '1e-2': 334,
                     '1e-1': 384, '1e0': 434, '1e1': 484, '1e2': 534}
timeStepIndex = timeStepIndexByDt[dtLabel]

# The index of a time (that must be larger than the time we trained our NNN) that we will give as initial composition to the NNN
initialAgeIndex = timeStepIndex + 1
#To compare to the first bbq step that is compatible with the NNN steps
# For 1001 timesteps from -10 to 2 [1e-6: 149, 1e-5: 199, 1e-4: 249, 1e-3: 299; 1e-2: 349; 1e-1: 399, 1e0:449 , 1e1: 499, 1e2: 549]
finalAgeIndex = timeStepIndex + 15

# Database_file_path is only important to get info about the existent isotopes in the nuclear network. It can reamin the same for different timesteps
database_file_path_mesa80 = zenodoDir + f'/python_scripts_for_analysis/CreateFigures/Figure3_density_maps/database_files/{netName}_database.csv'

# Dir with outputs for test (test_datasets)
testDataDirMesa80 = zenodoDir + f'/test_datasets/{netName}/{netName}_output_files/'

trainedModelBaseDir = zenodoDir + f'/trained_NNN_models/{netName}/different_timesteps/'
trainedModel = f'age_{dtLabel}_trainingdata_1e6_l1loss_layers_{layersNumForNet}_factor_8_{netName}'

os.makedirs(resultsDir + '/Results/Files', exist_ok=True)


bbqParamsMesa80 = findBbqParams(testDataDirMesa80,timeStepIndex,initialAgeIndex,finalAgeIndex,mesaDir,
                                database_file_path_mesa80,isotopesNum=isotopesNumForNet)


nnnParams = predictNNNcompsMultipleSteps(baseDir,testDataDirMesa80,trainedModelBaseDir,trainedModel,mesaDir,database_file_path_mesa80,timeStepIndex,
                                         initialAgeIndex,finalAgeIndex,isotopesNum=isotopesNumForNet)


LossesAndParams = computeNNNlosses(baseDir,testDataDirMesa80,initialAgeIndex,finalAgeIndex,bbqParamsMesa80,nnnParams)


end_time = time.time()
total_time = end_time - start_time
print(f"Total execution time: {total_time} seconds")
