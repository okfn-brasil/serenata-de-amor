import numpy as np
import pandas as pd


def find_sum_of_values(df, aggregator, property):
    '''
    Return a dataframe with the statistics of values from "property"
    aggregated by unique values from the column "aggregator"

    :params df: pandas dataframe to be sliced
    :params aggregator: dataframe column that will be
                        filtered by unique values
    :params property: dataframe column containing values to be summed
    :return: dataframe containing (for each aggregator unit):
        * property sum
        * property mean value
        * property max value
        * property mean value
        * number of occurences in total
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
        property_total = float(values[property].sum())
        occurences = float(values[property].count())

        result[total_label].append(property_total)
        result['occurences'].append(occurences)
        if occurences > 0:
            result[mean_label].append(property_total/occurences)
        else:
            result[mean_label].append(0)
        result[max_label].append(np.max(values[property]))
        result[min_label].append(np.min(values[property]))

    return pd.DataFrame(result).sort_values(by=aggregator)


def find_expenses_by_month(df, applicant_id):
    '''
    Return a dataframe with the sum of values of expenses by month
    of the congressperson of "applicant_id"

    :params df: pandas dataframe to be sliced
    :params applicant_id: unique id of the congress person
    :return: DataFrame with year, month (as integer), month (as string), sum,
        congressperson name, applicant id.
    '''

    fields = ['congressperson_name', 'year', 'month']
    df_applicant = df[df.applicant_id == applicant_id]
    results = df_applicant.groupby(fields).agg({'net_value': np.sum})
    return results.reset_index()


def find_expenses_by_subquota(df, applicant_id, year=None, month=None):
    '''
    Return a dataframe with the sum of values of expenses by subquotas
    of the congressperson of "applicant_id". Month and year arguments are
    optional. When ommitted this function sums all the expenses for the given
    congressperson.
    Parameters:
        :params df: pandas dataframe to be sliced
        :params applicant_id: unique id of the congress person
    '''

    df_applicant = df[df.applicant_id == applicant_id]
    if year:
        df_applicant = df_applicant[df_applicant.year == year]
    if month:
        df_applicant = df_applicant[df_applicant.month == month]

    fields = ['congressperson_name', 'subquota_description']
    results = df_applicant.groupby(fields).agg({'net_value': np.sum})
    results = results.reset_index()

    def add_col_to_pos(df, col, value, pos):
        df[col] = value
        cols = df.columns.tolist()
        cols.insert(pos, col)
        return df[cols[:-1]]

    if year:
        results = add_col_to_pos(results, 'year', year, 1)

    if month:
        results = add_col_to_pos(results, 'month', month, 2)

    return results
