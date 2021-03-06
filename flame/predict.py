#! -*- coding: utf-8 -*-

# Description    Flame Predict class
#
# Authors:       Manuel Pastor (manuel.pastor@upf.edu)
#
# Copyright 2018 Manuel Pastor
#
# This file is part of Flame
#
# Flame is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# Flame is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flame. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import importlib

from flame.util import utils, get_logger
# from flame.control import Control

LOG = get_logger(__name__)

class Predict:
    """
    TODO: Expand class docstring
    """

    def __init__(self, model, version, output_format=None):

        self.model = model
        self.version = version

        # # instance Control object
        # self.control = Control(model, version)
        # self.parameters = self.control.get_parameters()

        success, self.parameters = utils.get_parameters(model, version)
        if not success:
            LOG.critical('Unable to load model parameters. Aborting...')
            sys.exit()

        # add additional output formats included in the constructor 
        # this is requiered to add JSON format as output when the object is
        # instantiated from a web service call, requiring this output   
        if output_format != None:
            if output_format not in self.parameters['output_format']:
                self.parameters['output_format'].append(output_format)
 
        return

    def get_model_set(self):
        ''' Returns a Boolean indicating if the model uses external input
            sources and a list with these sources '''

        ext_input = False
        model_set = None

        if 'ext_input' in self.parameters:
            if self.parameters['ext_input']:
                if 'model_set' in self.parameters:
                    if len(self.parameters['model_set']) > 1:
                        model_set = self.parameters['model_set']
                        ext_input = True

        return ext_input, model_set

    def set_single_CPU(self):
        ''' Forces the use of a single CPU '''
        self.parameters['numCPUs'] = 1

    def run(self, input_source):
        ''' Executes a default predicton workflow '''

        results = {}

        # path to endpoint
        endpoint = utils.model_path(self.model, self.version)
        if not os.path.isdir(endpoint):

            LOG.debug('Unable to find model'
                      ' {} version {}'.format(self.model, self.version))

            results['error'] = 'unable to find model: ' + \
                self.model+' version: '+str(self.version)

        if 'error' not in results:
            # uses the child classes within the 'model' folder,
            # to allow customization of
            # the processing applied to each model
            modpath = utils.module_path(self.model, self.version)

            idata_child = importlib.import_module(modpath+".idata_child")
            apply_child = importlib.import_module(modpath+".apply_child")
            odata_child = importlib.import_module(modpath+".odata_child")

            LOG.debug('child modules imported: '
                      f' {idata_child.__name__},'
                      f' {apply_child.__name__},'
                      f' {odata_child.__name__}')

            # run idata object, in charge of generate model data from input
            idata = idata_child.IdataChild(self.parameters, input_source)
            results = idata.run()
            LOG.debug(f'idata child {idata_child.__name__} completed `run()`')

        if 'error' not in results:
            if 'xmatrix' not in results:
                LOG.debug(f'Failed to compute MDs')
                results['error'] = 'Failed to compute MDs'

        if 'error' not in results:
            # run apply object, in charge of generate a prediction from idata
            apply = apply_child.ApplyChild(self.parameters, results)
            results = apply.run()
            LOG.debug(f'apply child {apply_child.__name__} completed `run()`')

        # run odata object, in charge of formatting the prediction results or any error
        odata = odata_child.OdataChild(self.parameters, results)
        LOG.info('Prediction completed')
        return odata.run()
