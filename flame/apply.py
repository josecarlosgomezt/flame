#! -*- coding: utf-8 -*-

# Description    Flame Apply class
##
# Authors:       Manuel Pastor (manuel.pastor@upf.edu), Jose Carlos Gómez (josecarlos.gomez@upf.edu)
##
# Copyright 2018 Manuel Pastor
##
# This file is part of Flame
##
# Flame is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
##
# Flame is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with Flame.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import pickle
import os

from sklearn.metrics import mean_squared_error, matthews_corrcoef as mcc
from sklearn.metrics import f1_score
from sklearn.metrics import make_scorer
from sklearn.metrics import confusion_matrix
from flame.util import utils, get_logger
LOG = get_logger(__name__)


class Apply:

    def __init__(self, parameters, results):

        self.parameters = parameters
        self.results = results

        self.results['origin'] = 'apply'

    def external_validation(self):
        ''' when experimental values are available for the predicted compounds,
        run external validation '''

        ext_val_results = []
        
        # Ye are the y values present in the input file
        Ye = np.asarray(self.results["ymatrix"])

        # there are four variants of external validation, depending if the method
        # if conformal or non-conformal and the model is qualitative and quantitative

        if not self.parameters["conformal"]:

            # non-conformal 
            if not self.parameters["quantitative"]:
                
                # non-conformal & qualitative
                Yp = np.asarray(self.results["values"])

                if Ye.size == 0:
                    raise ValueError("Experimental activity vector is empty")
                if Yp.size == 0:
                    raise ValueError("Predicted activity vector is empty")

                # the use of labels is compulsory to inform the confusion matrix that
                # it must return a 2x2 confussion matrix. Otherwise it will fail when
                # a single class is represented (all TP, for example)
                TN, FP, FN, TP = confusion_matrix(
                    Ye, Yp, labels=[0, 1]).ravel()

                # protect to avoid warnings in special cases (div by zero)
                MCC = mcc(Ye, Yp)

                if (TP+FN) > 0:
                    sensitivity = (TP / (TP + FN))
                else:
                    sensitivity = 0.0

                if (TN+FP) > 0:
                    specificity = (TN / (TN + FP))
                else:
                    specificity = 0.0

                ext_val_results.append(('TP_ex',
                                        'True positives in external-validation',
                                        float(TP)))
                ext_val_results.append(('TN_ex',
                                        'True negatives in external-validation',
                                        float(TN)))
                ext_val_results.append(('FP_ex',
                                        'False positives in external-validation',
                                        float(FP)))
                ext_val_results.append(('FN_ex',
                                        'False negatives in external-validation',
                                        float(FN)))
                ext_val_results.append(('Sensitivity_ex',
                                        'Sensitivity in external-validation',
                                        float(sensitivity)))
                ext_val_results.append(('Specificity_ex',
                                        'Specificity in external-validation',
                                        float(specificity)))
                ext_val_results.append(('MCC_ex',
                                        'Mattews Correlation Coefficient in external-validation',
                                        float(MCC)))

            else:

                # non-conformal & quantitative
                Yp = np.asarray(self.results["values"])

                if Ye.size == 0:
                    raise ValueError("Experimental activity vector is empty")
                if Yp.size == 0:
                    raise ValueError("Predicted activity vector is empty")

                Ym = np.mean(Ye)
                nobj = len(Yp)

                SSY0_out = np.sum(np.square(Ym - Ye))
                SSY_out = np.sum(np.square(Ye - Yp))
                scoringP = mean_squared_error(Ye, Yp)
                SDEP = np.sqrt(SSY_out / (nobj))
                Q2 = 1.00 - (SSY_out / SSY0_out)

                ext_val_results.append(
                    ('scoringP_ex', 'Scoring P', scoringP))
                ext_val_results.append(
                    ('Q2_ex', 'Determination coefficient in cross-validation', Q2))
                ext_val_results.append(
                    ('SDEP_ex', 'Standard Deviation Error of the Predictions', SDEP))

            utils.add_result(self.results,
                             ext_val_results,
                             'external-validation',
                             'external validation',
                             'method',
                             'single',
                             'External validation results')

        else:
            # conformal external validation

            if not self.parameters["quantitative"]:
                
                # conformal & qualitative
                Yp = np.concatenate((np.asarray(self.results['c0']).reshape(
                    -1, 1), np.asarray(self.results['c1']).reshape(-1, 1)), axis=1)

                if Ye.size == 0:
                    raise ValueError("Experimental activity vector is empty")
                if Yp.size == 0:
                    raise ValueError("Predicted activity vector is empty")

                c0_correct = 0
                c1_correct = 0
                not_predicted = 0
                c0_incorrect = 0
                c1_incorrect = 0

                Ye1 = []
                Yp1 = []
                for i in range(len(Ye)):
                    real = float(Ye[i])
                    predicted = Yp[i]
                    if predicted[0] != predicted[1]:
                        Ye1.append(real)
                        if predicted[0]:
                            Yp1.append(0)
                        else:
                            Yp1.append(1)

                        if real == 0 and predicted[0] == True:
                            c0_correct += 1
                        if real == 0 and predicted[1] == True:
                            c0_incorrect += 1
                        if real == 1 and predicted[1] == True:
                            c1_correct += 1
                        if real == 1 and predicted[0] == True:
                            c1_incorrect += 1
                    else:
                        not_predicted += 1
                MCC = mcc(Ye1, Yp1)
                TN = c0_correct
                FP = c0_incorrect
                TP = c1_correct
                FN = c1_incorrect
                coverage = float((len(Yp) - not_predicted) / len(Yp))

                if (TP+FN) > 0:
                    sensitivity = (TP / (TP + FN))
                else:
                    sensitivity = 0.0
                if (TN+FP) > 0:
                    specificity = (TN / (TN + FP))
                else:
                    specificity = 0.0
                ext_val_results.append(('TP',
                                        'True positives in external-validation',
                                        float(TP)))
                ext_val_results.append(('TN',
                                        'True negatives in external-validation',
                                        float(TN)))
                ext_val_results.append(('FP',
                                        'False positives in external-validation',
                                        float(FP)))
                ext_val_results.append(('FN',
                                        'False negatives in external-validation',
                                        float(FN)))
                ext_val_results.append(('Coverage',
                                        'Conformal coverage in external-validation',
                                        float(coverage)))
                ext_val_results.append(('Sensitivity',
                                        'Sensitivity in external-validation',
                                        float(sensitivity)))
                ext_val_results.append(('Specificity',
                                        'Specificity in external-validation',
                                        float(specificity)))
                ext_val_results.append(('MCC',
                                        'Mattews Correlation Coefficient in external-validation',
                                        float(MCC)))
                utils.add_result(self.results,
                                 ext_val_results,
                                 'external-validation',
                                 'external validation',
                                 'method',
                                 'single',
                                 'External validation results')
            else:

                # conformal & quantitative
                Yp_lower = self.results['lower_limit']
                Yp_upper = self.results['upper_limit']

                mean_interval = np.mean(np.abs(Yp_lower) - np.abs(Yp_upper))
                inside_interval = (Yp_lower.reshape(-1, 1) <
                                   Ye) & (Yp_upper.reshape(-1, 1) > Ye)
                accuracy = len(inside_interval)/len(Ye)
                conformal_accuracy = float("{0:.2f}".format(accuracy))
                conformal_mean_interval = float(
                    "{0:.2f}".format(mean_interval))

                ext_val_results.append(('Conformal_mean_interval',
                                        'Conformal mean interval',
                                        conformal_mean_interval))
                ext_val_results.append(('Conformal_accuracy',
                                        'Conformal accuracy',
                                        conformal_accuracy))

                utils.add_result(self.results,
                                 ext_val_results,
                                 'external-validation',
                                 'external validation',
                                 'method',
                                 'single',
                                 'External validation results')

    def run_internal(self): 
        ''' 

        Runs prediction tasks using internally defined methods

        Most of these methods can be found at the stats folder

        '''

        # assume X matrix is present in 'xmatrix'
        X = self.results["xmatrix"]

        # use in single mol prdictions
        if X.ndim < 2:  # if flat array
            X = X.reshape(1, -1)  # to 1 row matrix

        # retrieve data and dimensions from results
        nobj, nvarx = np.shape(X)

        # check that the dimensions of the X matrix are acceptable
        if (nobj == 0) :
            LOG.error('No object found')
            self.results['error'] = 'No object found'
            return

        if (nvarx == 0):
            LOG.error('Failed to generate MDs')
            self.results['error'] = 'Failed to generate MDs'
            return

        # get model pickle
        model_file = os.path.join(self.parameters['model_path'],
                                  'model.pkl')

        LOG.debug(f'Loading model from pickle file, path: {model_file}')

        try:
            with open(model_file, "rb") as input_file:
                estimator = pickle.load(input_file)
        except FileNotFoundError:
            LOG.error(f'No valid model estimator found at: {model_file}')
            self.results['error'] = f'No valid model estimator found at: {model_file}'
            return

        # project the X matrix into the model and save predictions in self.results
        estimator.project(X, self.results)

        # if the input file contains activity values use them to run external validation 
        if 'ymatrix' in self.results:
            self.external_validation()

        return

    def run_R(self):
        ''' Runs prediction tasks using an importer KNIME workflow '''
        self.results['error'] = 'R toolkit is not supported in this version'
        return

    def run_KNIME(self):
        ''' Runs prediction tasks using R code '''
        self.results['error'] = 'KNIME toolkit is not supported in this version'
        return

    def run_custom(self):
        ''' Template to be overriden in apply_child.py

            Input: must be already present in self.results
            Output: add prediction results to self.results using the utils.add_result() method 

        '''

        self.results['error'] = 'custom prediction must be defined in the model apply_chlid class'
        return

    def run(self):
        ''' 

        Runs prediction tasks using the information present in self.results. 

        Depending on the modelingToolkit defined in self.parameters this task will use internal methods
        or make use if imported code in R/KNIME

        The custom option allows advanced uses to write their own function 'run_custom' method in 
        the model apply_child.py

        '''

        if self.parameters['modelingToolkit'] == 'internal':
            self.run_internal()
        elif self.parameters['modelingToolkit'] == 'R':
            self.run_R()
        elif self.parameters['modelingToolkit'] == 'KNIME':
            self.run_KNIME()
        elif self.parameters['modelingToolkit'] == 'custom':
            self.run_custom()
        else:
            self.results['error'] = 'Unknown prediction toolkit to run ', self.parameters['modelingToolkit']

        return self.results
