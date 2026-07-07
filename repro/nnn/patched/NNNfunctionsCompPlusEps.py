# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 13:44:41 2024

@author: aldana
"""

from torch.utils.data import Dataset
import pandas as pd
#import lightning.pytorch as pl
import pytorch_lightning as pl
from torch.nn import functional as F
import torch
from torch.utils.data import DataLoader, random_split

import os  # PATCH: parameterize paths/network size via environment

batch_size = 512 #Size of the group of data we train in every group

baseDir = os.environ.get('NNN_BASE_DIR', '/Research/NuclearNeuralNetworks')  # PATCH

database_file = os.environ.get('NNN_DATABASE_FILE', baseDir + '/Databases/mesa_80_1e-1_sec.csv')  # PATCH
# database_file = baseDir + '/Databases/mesa_151_1e-1_sec.csv'


database = pd.read_csv(database_file)
if 'mainSequence' in database_file:
    database.drop(columns = ['Age'], inplace = True)
else:
    database.drop(columns = ['Age'], inplace = True)
    if 'Ye' in database.columns:
        database.drop(columns = ['Ye'], inplace=True)

isotopesNum = int(os.environ.get('NNN_ISOTOPES_NUM', '80'))  # PATCH ## 151

intputSize = 2+isotopesNum #T,rho,80 isotopes abundances at the beginning of the age
outputSize = isotopesNum + 2 #80 isotopes abundances, eps_nuc, eps_nu after a timsestep equivalent to the age in bbq

#Defining a new class named bbqDataset based on the existing Pythorch class Dataset
class bbqDataset(Dataset):
    #Making the dataset and using basic objects from Dataset
    #__init__ is a special function in python that is automatically called when an object of the class is created. It is used to initialize the object's attributes and set up its initial state.
    def __init__(self, mode, trainingDataNum, transform=None, target_transform=None):  #Here we rewrite the function _init. transform and target_transform are residuals from MNIST
        if mode == 'train':
            self.database = torch.tensor(database.iloc[0:trainingDataNum].values, dtype = torch.float32)
        if mode == 'test':
            self.database = torch.tensor(database.iloc[trainingDataNum:].values, dtype=torch.float32)  # Use remaining data 
        self.transform = transform
        self.target_transform = target_transform
   
    #Getting the length of the dataset
    def __len__(self):
        return len(self.database)
    
    #Retrieving specific data points (defined by idx) from a database and convert them into PyTorch tensors. This is useful for running small batches on GPUs
    def __getitem__(self, idx):
        x = self.database[idx, :intputSize] #input for the NN
        y = self.database[idx, intputSize:] # final composition from bbq and EPSs
        return x, y

#Defining a new class named DataModule based on the existing Pythorch class LightningDataModule
class DataModule(pl.LightningDataModule):
  def __init__(self, trainingDataNum):
        super(DataModule, self).__init__() #Another step in initalization
        self.trainingDataNum = trainingDataNum
  #Preparing the relevant databases
  def setup(self, stage: str):
    dataset = bbqDataset('train', self.trainingDataNum) #create a variable of the type bbqDataset and put it in dataset by calling the _init that is defined in bbqDataset
    self.train, self.val = random_split(dataset, [int(len(dataset) * 0.95), len(dataset) - int(len(dataset) * 0.95)]) #Randomly splitting the database to a trainning and a validation set
    self.test = bbqDataset('test', self.trainingDataNum) #Defining the testings database 
      
  #Creating and returning a DataLoader object that will efficiently load and process training data in batches
  def train_dataloader(self):
      return DataLoader(self.train, batch_size=batch_size, pin_memory=True, shuffle = True, num_workers = 1)

  #Creating and returning a DataLoader object that will efficiently load and process validation data in batches
  def val_dataloader(self):
      return DataLoader(self.val, batch_size=batch_size, pin_memory=True, num_workers = 1)

  #Creating and returning a DataLoader object that will efficiently load and process test data in batches 
  def test_dataloader(self):
      return DataLoader(self.test, batch_size=batch_size, pin_memory=True)

#Defining a new class named nuclearNN based on the existing Pythorch class LightningModule. Contain the architectire of the NN
class nuclearNN(pl.LightningModule):

    def __init__(self, neuronsNumFactor = 1, layersNum = 4):
        super(nuclearNN, self).__init__() #Another step in initalization
        self.layersNum = layersNum
        
        self.layer_1 = torch.nn.Linear(intputSize, neuronsNumFactor*128)
        self.layer_2 = torch.nn.Linear(neuronsNumFactor*128, neuronsNumFactor*256)
        for i in range(3, layersNum):
            exec(f'self.layer_{i} = torch.nn.Linear(neuronsNumFactor*256, neuronsNumFactor*256)')

        exec(f'self.layer_{layersNum} = torch.nn.Linear(neuronsNumFactor*256, outputSize)')
        

    #Specifying how the input data flows through the network's layers and produces an output
    def forward(self, x):
        layersNum = self.layersNum
        batch_size, inputs = x.size()

        #Reshaping done to prepare the data for passing through the layers of the neural network
        x = x.view(batch_size, -1)
        
        
        for i in range(1, layersNum):
            x = eval(f'self.layer_{i}(x)')
            x = torch.relu(x)    
        
        x = eval(f'self.layer_{layersNum}(x)')
        #x = torch.log_softmax(x, dim=1) 
        
        # Apply log_softmax to the first 80 outputs
        first_80 = x[:, :isotopesNum] #predicted bbqComps
        last_2 = x[:, isotopesNum:] # Eps_nuc, Eps_Nu
        first_80_log_softmax = torch.log_softmax(first_80, dim=1)

        # Concatenate the normalized first 80 outputs with the unchanged last 2 outputs
        x = torch.cat([first_80_log_softmax, last_2], dim=1)
        
        return x

    #Measures the difference between two sets of data: nnComp (the predicted values from the neural network) and bbqComp (the target or true values).
    #The L1 loss measures the average absolute difference between the predictions and the true values

    def lossFunction(self, nnComp, bbqComp):
        # Separate outputs for the loss calculation
        nnComp_isotopes = nnComp[:, :isotopesNum]   # First 80 outputs
        nn_eps = nnComp[:, isotopesNum:]       # Last 2 outputs (eps_nuc and eps_nu)

        bbqComp_isotopes = bbqComp[:, :isotopesNum]
        bbq_eps = bbqComp[:, isotopesNum:]

        # Compute loss for the isotopes using log scale
        isotopes_loss = F.l1_loss(nnComp_isotopes, torch.log(bbqComp_isotopes))

        # Compute loss for the last two outputs without applying log
        eps_loss = F.l1_loss(nn_eps, bbq_eps)

        # Combine losses
        total_loss = isotopes_loss + eps_loss
        return total_loss



    #Training in a specific batch
    def training_step(self, batch, batch_idx):
        nnInput, bbqComp = batch
        nnComp = self.forward(nnInput)   
        loss = self.lossFunction(nnComp, bbqComp)
        self.log('train_loss', loss)
        return loss
    
    #Validating in a specific batch
    def validation_step(self, batch, batch_idx):
        nnInput, bbqComp = batch
        nnComp = self.forward(nnInput)  
        loss = self.lossFunction(nnComp, bbqComp)
        self.log('val_loss', loss)
        return loss

    #Testing in a specific batch
    def test_step(self, batch, batch_idx):
        nnInput, bbqComp = batch
        nnComp = self.forward(nnInput) 
        loss = self.lossFunction(nnComp, bbqComp)
        return loss

    #Specify and configure the optimizer for training the neural network. LR = learning rate, computes the gradients
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        return optimizer