import os
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd

from rosie.core import Core

DATAFRAME = pd.DataFrame({'number': (1, 2), 'text': ('one', 'two')})


class TestCore(TestCase):

    def setUp(self):
        self.adapter = MagicMock()
        self.adapter.dataset = DATAFRAME
        self.adapter.path = os.path.join('tmp', 'test')

    def test_init_with_unique_ids(self):
        settings = MagicMock()
        settings.UNIQUE_IDS = ['number']
        core = Core(settings, self.adapter)
        self.assertTrue(core.suspicions.equals(DATAFRAME[['number']]))

    def test_init_without_unique_ids(self):
        settings = MagicMock()
        settings.UNIQUE_IDS = None
        core = Core(settings, self.adapter)
        self.assertTrue(core.suspicions.equals(DATAFRAME))

    @patch.object(Core, 'load_trained_model')
    @patch.object(Core, 'predict')
    def test_call(self, mocked_predict, mocked_load):
        mocked_load.return_value = 'model'
        settings = MagicMock()
        settings.UNIQUE_IDS = ['number']
        settings.CLASSIFIERS = {'answer': 42, 'another': 13}
        core = Core(settings, self.adapter)
        core.suspicions = MagicMock()
        core()

        # assert load and predict was called for each classifier
        mocked_load.assert_has_calls((call(42), call(13)), any_order=True)
        mocked_predict.assert_has_calls((
            call('model', 'answer'),
            call('model', 'another')
        ), any_order=True)

        # assert suspicions.xz was created
        expected_path = os.path.join('tmp', 'test', 'suspicions.xz')
        core.suspicions.to_csv.assert_called_once_with(
            expected_path,
            compression='xz',
            encoding='utf-8',
            index=False
        )

    @patch('rosie.core.os.path.isfile')
    @patch('rosie.core.joblib')
    def test_load_trained_model_without_pickle(self, joblib, isfile):
        isfile.return_value = False

        ClassifierClass, classifier_instance = MagicMock(), MagicMock()
        ClassifierClass.return_value = classifier_instance
        ClassifierClass.__name__ = 'ClassifierMock'

        settings = MagicMock()
        settings.UNIQUE_IDS = ['number']
        core = Core(settings, self.adapter)
        core.load_trained_model(ClassifierClass)

        expected_path = os.path.join('tmp', 'test', 'classifiermock.pkl')
        classifier_instance.fit.assert_called_once_with(core.dataset)
        joblib.dump.assert_called_once_with(classifier_instance, expected_path)

    @patch('rosie.core.os.path.isfile')
    @patch('rosie.core.joblib')
    def test_load_trained_model_with_pickle(self, joblib, isfile):
        isfile.return_value = True

        ClassifierClass, classifier_instance = MagicMock(), MagicMock()
        ClassifierClass.return_value = classifier_instance
        ClassifierClass.__name__ = 'ClassifierMock'

        settings = MagicMock()
        settings.UNIQUE_IDS = ['number']
        core = Core(settings, self.adapter)
        core.load_trained_model(ClassifierClass)

        expected_path = os.path.join('tmp', 'test', 'classifiermock.pkl')
        self.assertFalse(classifier_instance.fit.called)
        joblib.load.assert_called_once_with(expected_path)

    def test_load_trained_model_for_subquota(self):
        ClassifierClass, classifier_instance = MagicMock(), MagicMock()
        ClassifierClass.return_value = classifier_instance
        ClassifierClass.__name__ = 'MonthlySubquotaLimitClassifier'

        settings = MagicMock()
        settings.UNIQUE_IDS = ['number']
        core = Core(settings, self.adapter)
        core.load_trained_model(ClassifierClass)

        classifier_instance.fit.assert_called_once_with(core.dataset)

    def test_predict(self):
        model = MagicMock()
        model.predict.return_value = np.array((1, -1), dtype=np.int)

        settings = MagicMock()
        settings.UNIQUE_IDS = ['number']
        core = Core(settings, self.adapter)
        core.predict(model, 'hypothesis')
        model.transform.assert_called_once_with(core.dataset)
        model.predict.assert_called_once_with(core.dataset)
        self.assertFalse(core.suspicions.iloc[0]['hypothesis'])
        self.assertTrue(core.suspicions.iloc[1]['hypothesis'])
