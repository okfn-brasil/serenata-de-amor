import numpy as np
import pandas as pd


def find_sum_of_values(df, aggregator, property):
    '''
    find_sum_of_values(df, aggregator, property)

    Ex: find_sum_of_values(data, 'congressperson_name', 'net_value')
    '''

    total_label = '{}_total'.format(property)
    max_label = '{}_max'.format(property)
    mean_label = '{}_mean'.format(property)
    min_label = '{}_min'.format(property)

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
        values = df[df[aggregator] == item]
        property_total = int(values[property].sum())
        occurences = int(values[property].count())

        result[total_label].append(property_total)
        result['occurences'].append(occurences)
        result[mean_label].append(property_total/occurences)
        result[max_label].append(np.max(values[property]))
        result[min_label].append(np.min(values[property]))

    return pd.DataFrame(result).sort_values(by=aggregator)
