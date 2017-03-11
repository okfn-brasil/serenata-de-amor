import numpy as np
import pandas as pd
from os import listdir
from os.path import join


def concatenate_data_dataframes(path):
    '''
    Return a concatenated dataframe with all ".xz" data available on
    path, disgegarding "companies" files.

    :params path: (str) path were .xz files are located
    '''
    files = [f for f in listdir(path) if f[-2::]=='xz']
    frames = []
    for file in files:
        if file[11:-3] != 'companies':
            frames.append(pd.read_csv(join(path, file) ,
                          parse_dates=[16],
                          dtype={'document_id': np.str,
                                 'congressperson_id': np.str,
                                 'congressperson_document': np.str,
                                 'term_id': np.str,
                                 'cnpj_cpf': np.str,
                                 'reimbursement_number': np.str}))
    return pd.concat(frames)



def find_sum_of_values(df, aggregator, value):
    '''
    Return a dataframe with the statistics of values from "value" property
    aggregated by unique values from the column "aggregator"

    :params df: pandas dataframe to be sliced
    :params aggregator: dataframe column that will be
                        filtered by unique values
    :params value: dataframe column containing values to be summed
    :return: dataframe containing (for each aggregator unit):
        * property sum
        * property mean value
        * property max value
        * property mean value
        * number of occurences in total
    '''

    total_label = '{}_total'.format(value)
    max_label = '{}_max'.format(value)
    mean_label = '{}_mean'.format(value)
    min_label = '{}_min'.format(value)

    result = {
        'occurences': [],
        aggregator: df[aggregator].unique(),
        max_label: [],
        mean_label: [],
        min_label: [],
        total_label: [],
    }

    for item in result[aggregator]:
        if isinstance(df[aggregator].iloc[0], str):
            item = str(item)
        data = df[df[aggregator] == item]
        property_total = float(data[value].sum())
        occurences = float(data[value].count())

        result[total_label].append(property_total)
        result['occurences'].append(occurences)
        if occurences > 0:
            result[mean_label].append(property_total/occurences)
        else:
            result[mean_label].append(0)
        result[max_label].append(np.max(data[value]))
        result[min_label].append(np.min(data[value]))

    return pd.DataFrame(result).sort_values(by=aggregator)


def find_sum_of_values_per_period(df, aggregator, period_aggregator, value):
    '''
    Return a dataframe with a matrix containing unique values of
    dataframe column "aggregator" and dataframe column "period_aggregator".
    The values added are the sum of the "value" column.

    :params df: pandas dataframe to be sliced
    :params aggregator: dataframe column that will be
                        filtered by unique values
    :params period_ggregator: dataframe column that will be
                              filtered by unique values and compared with
                              aggregator column
    :params value: dataframe column containing values to be summed
    :return: dataframe containing aggregator vs period_aggregator with
             the sum of "value".
    '''

    periods = df[period_aggregator].unique() #1,2,3,4...

    result = {
        aggregator: df[aggregator].unique(), #fulano, ciclano...
    }

    for period in periods:
        result[period] = []

    for item in result[aggregator]:
        data = df[df[aggregator]==item]
        for period in periods:
            data_per_period = data[data[period_aggregator]==period]
            result[period].append(data_per_period[value].sum())
    return pd.DataFrame(result).sort_values(by=aggregator)