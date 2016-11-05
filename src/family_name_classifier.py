import builtins

import pandas as pd
import numpy as np
import itertools
import unicodedata
import re
import collections
import random
import sklearn.feature_extraction
import sklearn.linear_model
import sklearn.cross_validation
import sklearn.externals.joblib
random.seed(0)


class FamilyNameClassifier:
    IGNORE_LIST = {'de', 'da', 'do', 'des', 'das', 'dos', 'e', 'dr', 'sobrinho', 'junior', 'neto', 'jr', 'filho'}
    NOT_ACCEPTABLE_CHARACTERS = re.compile(r'[^a-z ]')

    def __init__(self):
        self.vectorizer = None
        self.surname_counter = None
        self.total_surnames = None
        self.total_first_names = None
        self.model = None

    def tokenize(self, name):
        """"
        Simple tokenizer that normalizes and split a name by spaces.

        :param name: string
        :return: tokens: list
        """

        name = name.strip().lower()
        name = unicodedata.normalize('NFD', name)
        name = self.NOT_ACCEPTABLE_CHARACTERS.sub("", name)
        return [n for n in name.split(' ') if n not in self.IGNORE_LIST and len(n) > 1]

    def __count_names(self, relatives_dict):
        """
        Calculate some names statistics used internally.

        :param relatives_dict: dict
        :return:
        """
        self.surname_counter = collections.Counter()
        self.first_name_counter = collections.Counter()

        for son, parents in relatives_dict.items():
            tokens = self.tokenize(son)
            self.first_name_counter.update([tokens[0]])
            self.surname_counter.update(tokens[1:])

            for parent in parents:
                tokens = self.tokenize(parent)
                self.first_name_counter.update([tokens[0]])
                self.surname_counter.update(tokens[1:])

        self.total_surnames = sum([v for k, v in self.surname_counter.items()])
        self.total_first_names = sum([v for k, v in self.first_name_counter.items()])

    def is_first_name(self, name):
        """
        Says if a name (preprocessed by tokenize() function) is not a surname, based on the collected statistics.
        Used internally to remove composite names.

        :param name: string
        :return: is_first_name: boolean
        """
        prob_firstname = 1.0 * self.first_name_counter[name] / self.total_first_names
        prob_surname = 1.0 * self.surname_counter[name] / self.total_surnames
        return prob_firstname >= prob_surname

    def tokenize_surnames(self, name):
        """
        Returns a list of family names from a complete name string.

        :param name: string
        :return: surname_tokens: list
        """
        name_tokens = self.tokenize(name)
        for i, token in enumerate(name_tokens[1:]):
            if not self.is_first_name(token):
                return name_tokens[i + 1:]
        return []

    def feature_dict(self, name1, name2):
        """
        Collects the features used for the learning algorithm and returns
        it on a dictionary to use with scikit-learn DictVectorizer.

        :param name1: string
        :param name2: string
        :return: features_dictionary: dict
        """
        features = dict()
        tokens1 = self.tokenize_surnames(name1)
        tokens2 = self.tokenize_surnames(name2)

        common_names = set(tokens1).intersection(tokens2)
        surname_frequencies = [self.surname_counter[name] for name in common_names]

        if len(common_names) >= 1:
            features['n_common_surname>=1'] = True
        if len(common_names) >= 2:
            features['n_common_surname>=2'] = True
        if len(common_names) > 2:
            features['n_common_surname>2'] = True

        if len(surname_frequencies) > 0:
            features['least_frequent_common_surname'] = np.log(min(surname_frequencies) + 1)

        size_longest_name = max(len(tokens1), len(tokens2))
        if size_longest_name > 0:
            features['match_proportion'] = 1.0 * len(common_names) / size_longest_name

        return features

    def train(self, relatives_dict, n_negative_samples=100000, file_name_save=None):
        """
        Trains the algorithm using a provided dictionary of relatives names,
        where the values are a parent list and the keys are their son/doughter.
        The algorithm is trained using a random combination of the names as negatives
        examples.

        :param relatives_dict: dict
        :param n_negative_samples: int
        :param file_name_save: string
        :return:
        """
        print("Calculating name statistics.")
        self.__count_names(relatives_dict)

        positive_iterator = _positive_data_iterator(relatives_dict)
        negative_iterator = _random_negative_data_iterator(relatives_dict, n_negative_samples)
        names_iterator = itertools.chain(negative_iterator, positive_iterator)

        print("Generating dataset matrix.")
        # Iterates over the pairs of names to generate the features dictionaries
        self.vectorizer = sklearn.feature_extraction.DictVectorizer()
        dataset = self.vectorizer.fit_transform(map(lambda tup: self.feature_dict(tup[0], tup[1]),
                                                    names_iterator))
        n_positives = dataset.shape[0] - n_negative_samples
        target = [0] * n_negative_samples + [1] * n_positives

        print("Training")
        scoring = 'precision'
        self.model = sklearn.linear_model.LogisticRegressionCV(n_jobs=-1, scoring=scoring)
        self.model.fit(dataset, target)

        # Debug part:
        print("\nBest", scoring, "score:", np.max(np.average(self.model.scores_[1], axis=0)))
        importance_order = np.argsort(self.model.coef_[0, :])
        feat_names = self.vectorizer.get_feature_names()
        print("Trained bias weight:", self.model.intercept_[0])
        print("Trained weights of features:")
        for idx_feat in list(importance_order):
            print(feat_names[idx_feat], self.model.coef_[0, idx_feat])

        if file_name_save is not None:
            print("\nSaving...")
            self.save(file_name_save)

    def family_probability(self, name1, name2):
        """
        Using the trained model, gives a probability that two names belongs to the same family.

        :param name1: string
        :param name2: string
        :return:
        """
        x = self.vectorizer.transform(self.feature_dict(name1, name2))
        probabilities = self.model.predict_proba(x)
        return probabilities[0, 1]

    def same_family(self, group1, group2, threshold=0.5, return_match=False):
        """
        Given two family groups, it says if there is any combination of persons that
        may be relatives, using the trained algorithm and a probability threshold to decide.

        If return_match is true, this returns a tuple of the first pair of probable relatives found.

        :param group1: list of string
        :param group2: list of string
        :param threshold: float
        :param return_match: boolean
        :return: boolean or tuple
        """
        for person1, person2 in itertools.product(group1, group2):
            prob_relatives = self.family_probability(person1, person2)
            if prob_relatives >= threshold:
                if return_match:
                    return person1, person2
                return True

        if return_match:
            return None
        return False

    def save(self, file_name):
        """
        Saves the current (trained) object with scikit-learn Joblib method.

        :param file_name: string
        :return:
        """
        sklearn.externals.joblib.dump(self, file_name, compress=9)

    @builtins.staticmethod
    def load(file_name):
        """
        Loads a saved classifier.

        :param file_name: string
        :return: classifier
        """
        self = sklearn.externals.joblib.load(file_name)
        return self


def _positive_data_iterator(relatives_dict):
    """
    Just iterates over the parents data on the dictionary
    :param relatives_dict: dict
    :return: generator
    """
    for person, parents in relatives_dict.items():
        for parent in parents:
            yield (person, parent)


def _random_negative_data_iterator(relative_dict, max_sample, chance_parents=0.7):
    """
    Randomly picks two different persons from the relatives data and use it as an negative example.
    Parents of the second chosen person can be used randomly with probability
    given by chance_parents parameter. Any parent has the same chance.

    :param relative_dict: dict
    :param max_sample: int
    :param chance_parents: float
    :return: generator
    """

    keys = list(relative_dict.keys())
    for i in range(max_sample):
        [chosen_person1, chosen_person2] = random.sample(keys, 2)
        parents1 = set(relative_dict[chosen_person1])
        parents2 = set(relative_dict[chosen_person2])

        # Trying to avoid brothers
        common_parents = parents1.intersection(parents2)
        if len(common_parents) > 0:
            continue

        if random.random() < chance_parents:
            yield chosen_person1, random.choice(list(parents2))
        else:
            yield chosen_person1, chosen_person2


def _get_relatives():
    """"
        This is just a quick and dirty work around to get the family data to test the algorithm.
        This should be replaced as soon as possible.
    """
    print("Loading data.")
    relatives_pd = pd.read_csv('~/PycharmProjects/serenata-de-amor/data/2016-08-08-congressperson_relatives.xz',
                               dtype={'congressperson_id': np.str})
    relatives_pd.head()
    relatives_data = relatives_pd.to_dict(orient='records')
    current_year = pd.read_csv('~/PycharmProjects/serenata-de-amor/data/2016-08-08-current-year.xz',
                               dtype={'congressperson_id': np.str},
                               usecols=['congressperson_name', 'congressperson_id'])
    current_year.drop_duplicates(inplace=True)
    congressperson_names = current_year.to_dict(orient='records')
    names_index = {record['congressperson_id']: record['congressperson_name'] for record in congressperson_names}
    relatives_data = sorted(relatives_data, key=lambda dic: dic['congressperson_id'])

    relatives = dict()
    for idx, group in itertools.groupby(relatives_data, key=lambda dic: dic['congressperson_id']):
        if idx in names_index:
            name = names_index[idx]
            relatives[name] = list([d['relative_name'] for d in group])
    return relatives


def _family_to_list(person, parents_list):
    return [person] + parents_list


def _demo(classifier, relatives, threshold=0.7):
    """ A simple test that tries to find whole families using the parents data. """
    print("\nTrying to find families...")

    for ((person1, parents1), (person2, parents2)) in itertools.product(relatives.items(), relatives.items()):
        if person1 == person2:
            continue

        family1 = _family_to_list(person1, parents1)
        family2 = _family_to_list(person2, parents2)

        match = classifier.same_family(family1, family2, threshold, return_match=True)
        if match is not None:
            print("Same Family:", person1, "+", person2)
            print("\tReason:", match[0], "-", match[1])


if __name__ == '__main__':
    relatives = _get_relatives()
    classifier = FamilyNameClassifier()
    classifier.train(relatives, file_name_save="../data/family_classifier.bin")
    _demo(classifier, relatives)

