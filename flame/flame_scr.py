#! -*- coding: utf-8 -*-

# Description    Flame command
##
# Authors:       Manuel Pastor (manuel.pastor@upf.edu)
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
# along with Flame. If not, see <http://www.gnu.org/licenses/>.

import argparse
import pathlib
import sys

from flame.util import utils, get_logger
from flame.util import config, change_config_status

import flame.context as context
import flame.manage as manage

import logging

LOG = get_logger(__name__)


# TEMP: only to allow EBI model to run
def sensitivity(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return(tp / (tp+fn))


# TEMP: only to allow EBI model to run
def specificity(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return(tn / (tn+fp))


def configuration_warning() -> None:
    """ Checks if flame has been configured
     reading the config.yml and checking the config_status flag
    """
    config = utils._read_configuration()

    if not isinstance(config['config_status'], bool):
        raise ValueError('Wrong type found in config status.')

    if config['config_status']:
        return
    elif not config['config_status']:
        print("Flame hasn't been configured yet. "
              "Model repository may be wrong. "
              "Please use 'flame -c config' before using flame")
        sys.exit()  # force exit


def manage_cmd(args):
    '''
    Instantiates a Build object to build a model using the given input
    file (training series) and model (name of endpoint, eg. 'CACO2')
    '''

    version = utils.intver(args.version)

    if args.action == 'new':
        # check if config model repo path is correct
        utils.check_repository_path()
        success, results = manage.action_new(args.endpoint)
    elif args.action == 'kill':
        success, results = manage.action_kill(args.endpoint)
    elif args.action == 'remove':
        success, results = manage.action_remove(args.endpoint, version)
    elif args.action == 'publish':
        success, results = manage.action_publish(args.endpoint)
    elif args.action == 'list':
        success, results = manage.action_list(args.endpoint)
    elif args.action == 'import':
        success, results = manage.action_import(args.infile)
    elif args.action == 'export':
        success, results = manage.action_export(args.endpoint)
    elif args.action == 'refactoring':
        success, results = manage.action_refactoring(args.file)
    elif args.action == 'dir':
        success, results = manage.action_dir()
    elif args.action == 'info':
        success, results = manage.action_info(args.endpoint, version)
    elif args.action == 'results':
        success, results = manage.action_results(args.endpoint, version)
    else: 
        raise ValueError("Specified action does not exist.")

    print('flame : ', results)


def main():

    LOG.debug('-------------NEW RUN-------------\n')
    parser = argparse.ArgumentParser(
        description='Use Flame to either build a model from or apply a model to the input file.')

    parser.add_argument('-f', '--infile',
                        help='Input file.',
                        required=False)

    parser.add_argument('-e', '--endpoint',
                        help='Endpoint model name.',
                        required=False)

    parser.add_argument('-v', '--version',
                        help='Endpoint model version.',
                        required=False)

    parser.add_argument('-a', '--action',
                        help='Manage action.',
                        required=False)

    parser.add_argument('-c', '--command',
                        action='store',
                        choices=['predict', 'build', 'manage', 'config'],
                        help='Action type: \'predict\' or \'build\' or \'manage\'',
                        required=True)

    # parser.add_argument('-log', '--loglevel',
    #                     help='Logger level of verbosity',)

    parser.add_argument('-p', '--path',
                        help='Defines de new path for models repository.',
                        required=False)

    args = parser.parse_args()

    # init logger Level and set general config
    # another way around would be create a handler with the level
    # and append it to the global instance of logger

    # if args.loglevel:
    #     numeric_level = getattr(logging, args.loglevel.upper(), None)
    #     if not isinstance(numeric_level, int):
    #         raise ValueError('Invalid log level: {}'.format(args.loglevel))
    #     logging.basicConfig(level=numeric_level)

    # make sure flame has been configured before running any command, unless this command if used to 
    # configure flame
    if args.command != 'config':
        configuration_warning()

    if args.command == 'predict':

        if (args.endpoint is None) or (args.infile is None):
            print('flame predict : endpoint and input file arguments are compulsory')
            return

        version = utils.intver(args.version)

        command_predict = {'endpoint': args.endpoint,
                 'version': version,
                 'infile': args.infile}

        LOG.info(f'Starting prediction with model {args.endpoint}'
                 f' version {version} for file {args.infile}')

        success, results = context.predict_cmd(command_predict)
        # print('flame predict : ', success, results)

    elif args.command == 'build':

        if (args.endpoint is None) or (args.infile is None):
            print('flame build : endpoint and input file arguments are compulsory')
            return

        command_build = {'endpoint': args.endpoint, 'infile': args.infile}

        LOG.info(f'Starting building model {args.endpoint}'
                 f' with file {args.infile}')

        success, results = context.build_cmd(command_build)
        # print('flame build : ', success, results)

    elif args.command == 'manage':
        manage_cmd(args)

    elif args.command == 'config':
        config(args.path)
        change_config_status()

# import multiprocessing


if __name__ == '__main__':
    # used to reproduce speed problems in Linux platforms
    # multiprocessing.set_start_method('spawn')

    main()
