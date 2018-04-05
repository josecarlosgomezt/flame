#! -*- coding: utf-8 -*-

##    Description    Flame Predict class
##
##    Authors:       Manuel Pastor (manuel.pastor@upf.edu)
##
##    Copyright 2018 Manuel Pastor
##
##    This file is part of Flame
##
##    Flame is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation version 3.
##
##    Flame is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Flame. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time # only to simulate long runs

import util.utils as utils
from control import Control

class Predict:

    def __init__ (self, ifile, model, version, out_format='JSON'):

        self.ifile = ifile
        self.model = model
        self.out_format = out_format

        if version == None:
            self.version = 0
        else:
            try:
                self.version = int (version)
            except:
                self.version = 0
        return

    def run (self):
        ''' Executes a default predicton workflow '''

        # path to endpoint
        epd = utils.model_path(self.model, self.version)

        success = True
        results = ''

        #uses the child classes within the 'model' folder, to allow customization of
        #the processing applied to each model
        
        if not os.path.isdir(epd):
            return False, 'unable to find model: '+self.model+' version: '+str(self.version)
        
        try:
            sys.path.append(epd)
            from idata_child import IdataChild
            from apply_child import ApplyChild
            from odata_child import OdataChild

        except:
            raise
            #success = False
            #results = 'Error loading model classes:', sys.exc_info()[0]

        if not success:
            return success, results
        
        # instance Control object
        control = Control(self.model,self.version)
        parameters = control.get_parameters()

        # run idata object, in charge of generate model data from input
        idata = IdataChild (parameters, self.ifile)
        success, results = idata.run ()
        
        if not success:
            return success, results

        # run apply object, in charge of generate a prediction from idata
        apply = ApplyChild (parameters, results)
        success, results = apply.run ()
        
        if not success:
            return success, results

        # run odata object, in charge of formatting the prediction results
        odata = OdataChild (parameters, results, self.out_format)
        success, results = odata.run ()

        time.sleep(3)

        return success, results

