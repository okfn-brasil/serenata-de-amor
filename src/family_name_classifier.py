import itertools
import unicodedata
import re
import collections
import random

import pandas as pd
import numpy as np
import sklearn.feature_extraction
import sklearn.linear_model
import sklearn.cross_validation
import sklearn.metrics
import sklearn.externals.joblib


class FamilyNameClassifier:
    IGNORE_LIST = {'de', 'da', 'do', 'des', 'das', 'dos', 'e', 'dr', 'sobrinho', 'junior', 'neto', 'jr', 'filho'}
    NOT_ACCEPTABLE_CHARACTERS = re.compile(r'[^a-z ]')

    def __init__(self):
        """
        A algorithm used to decide if two persons are from the same family given only their full names.
        It takes into account surnames in common and its frequencies. Machine learning is used to make the decision.
        """
        self.vectorizer = None
        self.surname_counter = None
        self.model = None
        self.total_surnames = 0
        self.total_first_names = 0
        self.surname_counter = collections.Counter()
        self.first_name_counter = collections.Counter()

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

    def __update_names_statistics(self, names_list):
        """
        Updates some names statistics used internally.

        :param names_list: list
        """
        for name in names_list:
            tokens = self.tokenize(name)
            first_name = tokens[0]
            surnames = tokens[1:]
            self.first_name_counter.update([first_name])
            self.surname_counter.update(surnames)
            self.total_first_names += 1
            self.total_surnames += len(surnames)

    def is_first_name(self, name):
        """
        Says if a name (preprocessed by tokenize() function) is not a surname, based on the collected statistics.
        Used internally to remove composite names.

        :param name: string
        :return: is_first_name: boolean
        """
        prob_first_name = self.first_name_counter[name] / self.total_first_names
        prob_surname = self.surname_counter[name] / self.total_surnames
        return prob_first_name > prob_surname

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
        if len(common_names) >= 1:
            features['n_common_surname>=1'] = True
        if len(common_names) >= 2:
            features['n_common_surname>=2'] = True
        if len(common_names) > 2:
            features['n_common_surname>2'] = True

        surname_frequencies = np.array([self.surname_counter[name] for name in common_names])
        if len(surname_frequencies) > 0:
            features['min_log_frequency_in_common_surname'] = np.log(np.min(surname_frequencies) + 1)
            features['average_log_frequency_in_common_surnames'] = np.average(np.log(surname_frequencies + 1))

        size_longest_name = max(len(tokens1), len(tokens2))
        if size_longest_name > 0:
            features['match_proportion'] = len(common_names) / size_longest_name
        return features

    def __to_feature_list(self, relatives_tuples):
        """
        Internal utility function, gets a list of pairs of names and applies the feature_dict() function on it.

        :param relatives_tuples: [(name1, name2), (name1, name2), ...]
        :return features_list: list of dict features
        """
        features_list = [self.feature_dict(person1, person2) for person1, person2 in relatives_tuples]
        return features_list

    def __sklearn_fit(self, dataset, target, scoring):
        """
        Trains the scikit-learn part using a provided dataset matrix, a target vector and a scoring method,
        used to select parameters.

        :param dataset: numpy vector
        :param target: numpy vector
        :param scoring: scoring method compatible with scikit-learn
        """
        self.model = sklearn.linear_model.LogisticRegressionCV(Cs=[0.1, 1, 10, 100], n_jobs=-1, scoring=scoring)
        self.model.fit(dataset, target)

    def train(self, relatives_dict, full_names_list, n_negative_samples=100000, file_name_save=None,
              kfolds_eval=5, scoring="precision"):
        """
        Trains the algorithm using a provided dictionary of relatives names,
        where the values are a parent list and the keys are their son/doughter.
        The algorithm is trained using a random combination of the names as negatives
        examples. As an complement, a list of full names of persons (without relatives information)
        need to be provided to generate some statistics to be use with the algorithm.
        The relatives_dict names in are not used to collect those statistics to avoid biasing the evaluation.

        The kfolds_eval parameter is the number of evaluations performed using the kFold methodology
        (a zero value can be used to skip this step).
        The scoring parameter is given to scikit-learn to select some parameters.

        :param relatives_dict: {"son_daughter_fullname": ["parent1_fullname", "parent2_fullname", ...]}
        :param full_names_list: list (or any iterable)
        :param n_negative_samples: int
        :param file_name_save: string
        :param kfolds_eval: int
        :param scoring: scoring method compatible with scikit-learn
        """
        # Preparing data for training
        positive_iterator = _positive_data_iterator(relatives_dict)
        negative_iterator = _random_negative_data_iterator(relatives_dict, n_negative_samples)
        dataset_names_list = list(negative_iterator) + list(positive_iterator)

        # Preparing target set
        n_positives = len(dataset_names_list) - n_negative_samples
        target = [0] * n_negative_samples + [1] * n_positives
        target = np.array(target)

        self.__update_names_statistics(full_names_list)

        # Preparing dataset matrix to the training
        features_list = self.__to_feature_list(dataset_names_list)
        self.vectorizer = sklearn.feature_extraction.DictVectorizer()
        dataset = self.vectorizer.fit_transform(features_list)

        if kfolds_eval > 1:
            kfolds = sklearn.cross_validation.StratifiedKFold(target, kfolds_eval)
            print("Evaluating...")
            for k, (ids_train, ids_test) in enumerate(kfolds):
                train = dataset[ids_train, :]
                train_target = target[ids_train]

                test = dataset[ids_test, :]
                test_target = target[ids_test]

                self.__sklearn_fit(train, train_target, scoring)

                print("Train report #", k + 1)
                train_predicted = self.model.predict(train)
                print(sklearn.metrics.classification_report(train_target, train_predicted, digits=4))

                print("Test report #", k+1)
                test_predicted = self.model.predict(test)
                print(sklearn.metrics.classification_report(test_target, test_predicted, digits=4))
                print("=====================")

        print("Final training...")
        self.__sklearn_fit(dataset, target, scoring)

        # Debug part:
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
        Given two family groups, it says if there is any combination of persons could be from the same family,
        using the trained algorithm and a probability threshold to decide.

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
                else:
                    return True

        if return_match:
            return None
        else:
            return False

    def save(self, file_name):
        """
        Saves the current (trained) object with scikit-learn Joblib method.

        :param file_name: string
        """
        sklearn.externals.joblib.dump(self, file_name, compress=9)


def load_classifier(file_name):
    """
    Utility function, used to load a saved FamilyNameClassifier object.

    :param file_name: string
    :return: FamilyNameClassifier object
    """
    self = sklearn.externals.joblib.load(file_name)
    return self


def _positive_data_iterator(relatives_dict):
    """
    Just iterates over the parents data on the dictionary.

    :param relatives_dict: {"son_daughter_fullname": ["parent1_fullname", "parent2_fullname", ...]}
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
    relatives_pd = pd.read_csv('~/PycharmProjects/serenata-de-amor/data/2016-11-09-congressperson_relatives.xz',
                               dtype={'congressperson_id': np.str})
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


def _get_full_names_list(file_full_names):
    """
    Opens a given file with one name per line and loads it in a list.

    :return: full_names_list: list
    """
    with open(file_full_names) as f:
        full_names_list = f.readlines()
    return full_names_list


def _family_to_list(person, parents_list):
    return [person] + parents_list


def _relatives_dict_to_list(relatives_dict):
    """
    Utility internal function that takes a dictionary of relatives and returns an iterable of names.

    :param relatives_dict: {"son_daughter_fullname": ["parent1_fullname", "parent2_fullname", ...]}
    """
    return itertools.chain.from_iterable([_family_to_list(person, parents)
                                         for person, parents in relatives_dict.items()])


def _family_finder_demo(classifier, relatives_dict, threshold=0.7):
    """
    A simple test that tries to find whole families using the parents data, using a trained classifier
    and probability threshold.

    :param classifier: FamilyNameClassifier object
    :param relatives_dict: {"son_daughter_fullname": ["parent1_fullname", "parent2_fullname", ...]}
    :param threshold: float
    """
    print("\nTrying to find families...")
    families_items = list(relatives_dict.items())
    n_pairs = len(families_items)
    for family1_id in range(n_pairs):
        for family2_id in range(family1_id + 1, n_pairs):
            person1, parents1 = families_items[family1_id]
            person2, parents2 = families_items[family2_id]

            family1 = _family_to_list(person1, parents1)
            family2 = _family_to_list(person2, parents2)

            match = classifier.same_family(family1, family2, threshold, return_match=True)
            if match is not None:
                print("Same Family:", person1, "+", person2)
                print("\tReason:", match[0], "-", match[1])


def _iterative_demo(classifier):
    """
    Simple utility function to play with a trained classifier.

    :param classifier: FamilyNameClassifier object
    """
    try:
        while True:
            print("")
            name1 = input("Type name 1: ")
            name2 = input("Type name 2: ")
            print("Family Probability:", classifier.family_probability(name1, name2))
            print("Person 1 Surname:", classifier.tokenize_surnames(name1))
            print("Person 2 Surname:", classifier.tokenize_surnames(name2))
            print("Features:", classifier.feature_dict(name1, name2))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    random.seed(0)
    np.random.seed(0)
    relatives = _get_relatives()
    full_names = _get_full_names_list("../data/full_names_list.txt")
    family_classifier = FamilyNameClassifier()
    family_classifier.train(relatives, full_names, file_name_save="../data/family_classifier.bin")
    family_classifier = load_classifier("../data/family_classifier.bin")
    _family_finder_demo(family_classifier, relatives, threshold=0.8)
    _iterative_demo(family_classifier)
