import pytest

import io
import os
import json

import numpy as np

from flame import manage
from flame import build
from flame import predict

MODEL_REPOSITORY = '/home/testmodels'
MODEL_NAME = 'FULLMODEL'
SDF_FILE_NAME = os.path.join(os.path.dirname(__file__), 'minicaco.sdf')
FIXED_RESULTS = os.path.join(os.path.dirname(__file__), 'results_file.json')


@pytest.fixture
def make_model():
    manage.set_model_repository(MODEL_REPOSITORY)
    return manage.action_new(MODEL_NAME)


@pytest.fixture
def build_model():
    builder = build.Build(MODEL_NAME)
    builder.parameters['tune'] = False
    return builder.run(SDF_FILE_NAME)


@pytest.fixture
def fixed_results():

    with open(FIXED_RESULTS) as f:
        results = json.load(f)
    return np.array(results['values'])


def test_new_build_predict(make_model, build_model, fixed_results):
    """test predict comparing results"""

    make_status, message = make_model
    assert (make_status is True) or (message == 'This endpoint already exists')

    build_status, _ = build_model
    assert build_status is True

    predictor = predict.Predict(MODEL_NAME, 0)
    _, results_str = predictor.run(SDF_FILE_NAME)

    prediction_results_dict = json.load(io.StringIO(results_str))
    result_values = np.array(prediction_results_dict['values'])

    assert all(np.isclose(fixed_results, result_values, rtol=1e-4))
