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

def find_spends_by_month(df, applicant_id):
    '''
    Return a dataframe with the sum of values of spends by month
    of the congress person of "applicant_id"

    :params df: pandas dataframe to be sliced
    :params applicant_id: unique id of the congress person 
        
    Ex: find_spends_by_month(df, 731)
    Result dataframe contains:
        - 1/Jan sum
        - 2/Feb sum
        - 3/Mar sum
        - 4/Apr sum
        - 5/May sum
        - 6/Jun sum
        - 7/Jul sum
        - 8/Aug sum
        - 9/Sep sum
        - 10/Oct sum
        - 11/Nov sum
        - 12/Dec sum
        - name
    '''

    months={1:"Jan",
            2:"Feb",
            3:"Mar",
            4:"Apr",
            5:"May",
            6:"Jun",
            7:"Jul",
            8:"Aug",
            9:"Sep",
            10:"Oct",
            11:"Nov",
            12:"Dec"}
    df_applicant = df[df.applicant_id == applicant_id]
    result = {
        "name":df_applicant["congressperson_name"].unique()
    }
       
    for m in months.keys():
        data = df_applicant[df.month == m]
        result["{:>02}".format(m) + "/" + months[m]] = data.net_value.sum()

    return pd.DataFrame([result])

def find_spends_by_subquota(df, applicant_id, month=None):
    '''
    Return a dataframe with the sum of values of spends by subquotas
    of the congress person of "applicant_id" and month "month"
    Parameters:
        :param sdf: pandas dataframe to be sliced
        :params applicant_id: unique id of the congress person
    '''


    df_applicant = df[df.applicant_id == applicant_id]
    
    result = {
        "name":df_applicant["congressperson_name"].unique(),
        "total": 0  
    }
    if month != None:
        df_applicant = df_applicant[df_applicant.month==month]

    for c in df["subquota_description"].unique():
        data = df_applicant[df.subquota_description == c]
        result[c] = data.net_value.sum()
        result["total"] += result[c]
        
    return pd.DataFrame([result])
