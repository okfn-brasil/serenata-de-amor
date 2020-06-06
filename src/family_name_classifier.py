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
import sklearn.preprocessing


class FamilyNameClassifier:
    IGNORE_LIST = {'de', 'da', 'do', 'des', 'das', 'dos', 'e', 'dr', 'sobrinho', 'junior', 'neto', 'jr', 'filho'}
    NOT_ACCEPTABLE_CHARACTERS = re.compile(r'[^a-z ]')

    def __init__(self, names_cut_off_frequency=10):
        """
        An algorithm used to decide if two persons are from the same family given only their full names.
        It takes into account surnames in common and its frequencies. Machine learning is used to make the decision.

        :param names_cut_off_frequency: used in is_first_name() method to avoid over pruning.
        :type names_cut_off_frequency: int
        """
        self.names_cut_off_frequency = names_cut_off_frequency
        self.vectorizer = None
        self.surname_counter = None
        self.model = None
        self.total_surnames = 0
        self.total_first_names = 0
        self.total_second_names = 0
        self.surname_counter = collections.Counter()
        self.first_name_counter = collections.Counter()
        self.second_name_counter = collections.Counter()

    def tokenize(self, name):
        """
        A simple tokenizer function that normalizes and split a name by spaces and ignores tokens of size 1.

        :param name: string to tokenize
        :type name: str
        :return: tokens
        :rtype: list
        """

        name = name.strip().lower()
        name = unicodedata.normalize('NFD', name)
        name = self.NOT_ACCEPTABLE_CHARACTERS.sub("", name)
        return [n for n in name.split(' ') if n not in self.IGNORE_LIST and len(n) > 1]

    def __update_names_statistics(self, names_list):
        """
        Updates some names statistics used internally.

        :param names_list: list of names to process.
        :type names_list: list
        """
        for name in names_list:
            tokens = self.tokenize(name)

            first_name = tokens[0]
            self.total_first_names += 1
            self.first_name_counter.update([first_name])

            # Only consider second names if there is more than two names
            if len(tokens) > 2:
                second_name = tokens[1]
                surnames = tokens[2:]
                self.total_second_names += 1
                self.second_name_counter.update([second_name])
            else:
                surnames = tokens[1:]

            self.surname_counter.update(surnames)
            self.total_surnames += len(surnames)

    def is_first_name(self, name):
        """
        Says if a name (preprocessed by tokenize() function) is not a surname, based on the collected statistics.
        Used internally to remove composite names. If a name occurred few times
        (based on the names_cut_off_frequency attribute), never says that it is first name.

        :param name: processed name to evaluate
        :type name: str
        :return: a boolean saying if the name can be analyzed as first name
        :rtype: bool
        """
        if self.first_name_counter[name] < self.names_cut_off_frequency \
                and self.second_name_counter[name] < self.names_cut_off_frequency:
            return False
        prob_first_name = self.first_name_counter[name] / self.total_first_names
        prob_surname = self.surname_counter[name] / self.total_surnames
        prob_second_name = self.second_name_counter[name] / self.total_second_names
        return prob_first_name > prob_surname or prob_second_name > prob_surname

    def tokenize_surnames(self, name):
        """
        Applies the whole name processing, returning a list of family names
        from a complete name string, removing first names and composite names.

        :param name: name to tokenize.
        :type name: str
        :return: list of family name tokens.
        :rtype: list
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
        The order of the arguments does not matter.

        :param name1: first person's fullname.
        :type name1: str
        :param name2: second person's fullname.
        :type name2: str
        :return: dictionary of features.
        :rtype: dict
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
            features['min_log_frequency_in_common_surname'] = np.log10(np.min(surname_frequencies) + 1)
            features['average_log_frequency_in_common_surnames'] = np.average(np.log10(surname_frequencies + 1))

        size_longest_name = max(len(tokens1), len(tokens2))
        if size_longest_name > 0:
            features['match_proportion'] = len(common_names) / size_longest_name
        return features

    def __to_feature_list(self, relatives_tuples):
        """
        Internal utility function, gets a list of pairs of names and applies the feature_dict() function on it.

        :param relatives_tuples: [(name1, name2), (name1, name2), ...]
        :type relatives_tuples: list
        :return: list of dict features
        :rtype: list
        """
        features_list = [self.feature_dict(person1, person2) for person1, person2 in relatives_tuples]
        return features_list

    def __sklearn_fit(self, dataset, target, scoring):
        """
        Trains the scikit-learn part using a provided dataset matrix, a target vector and a scoring method,
        used to select parameters.

        :param dataset: training dataset matrix.
        :type dataset: np.array
        :param target: training target vector.
        :type target: np.array
        :param scoring: scoring method compatible with scikit-learn (e.g. 'precision').
        :type scoring: str
        """
        self.model = sklearn.linear_model.LogisticRegressionCV(Cs=[0.1, 1, 10, 100], n_jobs=-1, scoring=scoring)
        self.scaler = sklearn.preprocessing.MinMaxScaler()
        dataset = self.scaler.fit_transform(dataset)
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
        :type relatives_dict: dict
        :param full_names_list: list (or any iterable)
        :type full_names_list: list
        :type n_negative_samples: int
        :type file_name_save: string
        :type kfolds_eval: int
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
        self.vectorizer = sklearn.feature_extraction.DictVectorizer(sparse=False)
        dataset = self.vectorizer.fit_transform(features_list)

        if kfolds_eval > 1:
            kfolds = sklearn.cross_validation.StratifiedKFold(target, kfolds_eval)
            avg = 0
            print("Evaluating...")
            for k, (ids_train, ids_test) in enumerate(kfolds):
                train = dataset[ids_train, :]
                train_target = target[ids_train]

                test = dataset[ids_test, :]
                test_target = target[ids_test]

                self.__sklearn_fit(train, train_target, scoring)

                print("Train report #", k + 1)
                train_predicted = self.model.predict(self.scaler.transform(train))
                print(sklearn.metrics.classification_report(train_target, train_predicted, digits=4))

                print("Test report #", k+1)
                test_predicted = self.model.predict(self.scaler.transform(test))
                print(sklearn.metrics.classification_report(test_target, test_predicted, digits=4))
                print("=====================")
                avg += sklearn.metrics.precision_score(test_target, test_predicted)

            print("Average test precision:", avg/kfolds_eval)
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

        :param name1: first person's fullname.
        :type name1: str
        :param name2: second person's fullname.
        :type name2: str
        :return: confidence of the algorithm that the two persons are from the same family.
        :rtype: float
        """
        x = self.scaler.transform(self.vectorizer.transform(self.feature_dict(name1, name2)))
        probabilities = self.model.predict_proba(x)
        return probabilities[0, 1]

    def same_family(self, group1, group2, threshold=0.5, return_match=False):
        """
        Given two family groups, it says if there is any combination of persons could be from the same family,
        using the trained algorithm and a probability threshold to decide.

        If return_match is true, this returns a tuple of the first pair of probable relatives found.

        :param group1: list of names from the first family
        :type group1: list
        :param group2: list of names from the second family
        :type group2: list
        :param threshold: probability threshold
        :type threshold: float
        :type return_match: boolean
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

        :param file_name: path to save the model
        :type file_name: str
        """
        sklearn.externals.joblib.dump(self, file_name, compress=5)


def load_classifier(file_name):
    """
    Utility function, used to load a saved FamilyNameClassifier object.

    :param file_name: path to load the model
    :type file_name: str
    :rtype: FamilyNameClassifier
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


def _get_relatives(list_ceap_files, relatives_file):
    """"
    Utility function that reads the data needed to the training the algorithm and returns a dict with it.
    The relative file is generated by get_family_names.py script (typically *congressperson_relatives.xz)
    and the ceap files (*current-year.xz , *last-year.xz, ...) are obtained just running the setup.py script.

    :param list_ceap_files: list of ceap files names
    :param relatives_file: relatives file name
    :return relatives_dict: {"son_daughter_fullname": ["parent1_fullname", "parent2_fullname", ...]}
    """
    print("Loading data.")
    ceaps_list = list()
    for file_name in list_ceap_files:
        ceap = pd.read_csv(file_name,
                           dtype={'congressperson_id': np.str},
                           usecols=['congressperson_name', 'congressperson_id'])
        ceaps_list.append(ceap)
    ceaps_pd = pd.concat(ceaps_list)
    ceaps_pd.drop_duplicates(inplace=True)

    relatives_pd = pd.read_csv(relatives_file, dtype={'congressperson_id': np.str})

    # Join and aggregation to turn the dataframes into the dict of relatives
    join = pd.merge(relatives_pd, ceaps_pd, left_on='congressperson_id', right_on='congressperson_id')
    group_by = join.groupby('congressperson_name')
    relatives_dict = group_by.apply(lambda x: list(x['relative_name'])).to_dict()

    return relatives_dict


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
    relatives = _get_relatives(['../data/2016-08-08-last-year.xz', '../data/2016-08-08-current-year.xz'],
                               '../data/2016-11-09-congressperson_relatives.xz')
    full_names = _get_full_names_list("../data/full_names_list.txt")
    family_classifier = FamilyNameClassifier()
    family_classifier.train(relatives, full_names, file_name_save="../data/family_classifier.bin")
    family_classifier = load_classifier("../data/family_classifier.bin")
    _family_finder_demo(family_classifier, relatives, threshold=0.75)
    _iterative_demo(family_classifier)
