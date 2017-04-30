import os.path

import numpy as np
from sklearn.externals import joblib

class Core:
    """
    This is Rosie's core object: it implements a generic pipeline to collect
    data, clean and normalize it, analyzies the data and output a dataset with
    suspicions. It's initialization module takes a settings module and an
    adapter.

    The settings module should have three constants:
    * CLASSIFIERS (dict) with pairs of human readable name (snake case) for
    each classifier and the object (class) of the classifiers.
    * UNIQUE_IDS (str or iterable) with the column(s) that should be taken as
    unique identifiers if the main dataset of each module.
    * VALUE (str) with the column that should be taken as the total net value
    of the transaction represented by each row of the datset.

    The adapter should be an object with:
    * A `dataset` property with the main dataset to be analyzed;
    * A `path` property with the path to the datasets (where the output will be
    saved).
    """

    def __init__(self, settings, adapter):
        self.settings = settings
        self.dataset = adapter.dataset
        self.data_path = adapter.path
        self.suspicions = self.dataset[self.settings.UNIQUE_IDS].copy()

    def __call__(self):
        for name, classifier in self.settings.CLASSIFIERS.items():
            model = self.load_trained_model(classifier)
            self.predict(model, name)

        output = os.path.join(self.data_path, 'suspicions.xz')
        kwargs = dict(compression='xz', encoding='utf-8', index=False)
        self.suspicions.to_csv(output, **kwargs)

    def load_trained_model(self, classifier):
        filename = '{}.pkl'.format(classifier.__name__.lower())
        path = os.path.join(self.data_path, filename)

        # palliative: this outputs a model too large for joblib
        if classifier.__name__ == 'MonthlySubquotaLimitClassifier':
            model = classifier()
            model.fit(self.dataset)

        else:
            if os.path.isfile(path):
                model = joblib.load(path)
            else:
                model = classifier()
                model.fit(self.dataset)
                joblib.dump(model, path)

        return model

    def predict(self, model, name):
        model.transform(self.dataset)
        prediction = model.predict(self.dataset)
        self.suspicions[name] = prediction
        if prediction.dtype == np.int:
            self.suspicions.loc[prediction == 1, name] = False
            self.suspicions.loc[prediction == -1, name] = True
