'''
Modal calculation, incorporating
reliability scores
v1.0
11/26/2017

This script takes the output from Kevin's
current "cleaning" script - a "placeholder" CSV file -
and outputs "reliability" scores for each 
volunteer. The reliability score for a given
volunteer is the average of the Cohen's Kappa
scores between that volunteer and every other
volunteer multiplied by the log of the number
of classifications completed by that user. The scale
of the reliability score is fairly meaningless; the 
score is meant to be used to rank raters, not really 
for deep interpretation.

Dependencies:

Without getting too specific, this script
should work with most versions of numpy and pandas.
It is highly recommended that 
you run Python >= 3.x and not Python 2.x.
'''

# If still running Python 2.x, need floating-point
# division, not integer division
import sys
if sys.version_info.major == 2:
    from __future__ import division

import os

import pandas as pd
import numpy as np
from statistics import mode, StatisticsError

def rev_sorted(a):
    '''Basically a wrapper to pass `reverse` argument using df.apply'''
    return sorted(a, reverse=True)

def top_n_raters(a, n=2):
    '''Grab first n elements from iterable'''
    return a[:n]

def rating_ratio(a):
    '''Used to find the reliability score ratio between two raters...
    
    returns None if only one rater available... don\'t need
    to investigate the Nones since there was only one rater'''
    try:
        return a[0]/a[1]
    except IndexError:
        return None

def iter_until(answers, ranks, answer_limit={'Yes', 'No'}, rank_limit=1000):
    '''Iterate through list of answers and ranks to find satisfactory answer
    
    Example:
        >>> answers = ["I can't figure this one out.", 'Yes']
        >>> rater_ranks = [1, 23]
        >>> iter_until(answers, rater_ranks)
        {'answer': 'Yes', 'index': 1, 'rank': 23}
    '''
    if not all(isinstance(x, (list, tuple)) for x in [answers, ranks]):
        raise ValueError('Convert `answers` and `rank` to list or tuple')

    together = list(zip(answers, ranks))

    curr_val, curr_rank = together[0]
    next_idx = 1

    while curr_val not in answer_limit and curr_rank < rank_limit:
        try:
            curr_val, curr_rank = together[next_idx]
            next_idx += 1
            could_not_find_flag = False
        except IndexError:
            could_not_find_flag = True
            break
    data = {'next_best_answer': curr_val, 'next_best_rank': curr_rank,
            'index': next_idx-1, 'could_not_find_flag': could_not_find_flag}
    return data

os.chdir('/path/to/intermediate')

# Read a placeholder file
df = pd.read_csv('<PLACEHOLDER>.csv')

# Consider only those images "retired"
# i.e. have been seen >= 4 times by separate raters
df = df[df['Retired'] == 'Retired']

# Read in rater reliability ratings
# should look like 'reliability_scores_YYYY_MM_DD.csv'.
ratings_df = pd.read_csv('<RELIABILITY_SCORES>.csv')

# Keep only those raters that have a reliability score
# Most should, but keeping this just for good measure
ratings_df = ratings_df[ratings_df['reliability_score'].notnull()]

# Join each rater's agreement index score with each image they've seen (each row)
df = pd.merge(df, ratings_df,
            left_on='User_Name',
            right_on='index',
            how='left')

# Hmmm... will have to find out a way to handle those without a 
# reliability score... for now, exclude from both df and ratings_df
# I don't think this should be a huge issue. This would only 
# be an issue in the case of a deed being retired by four
# new volunteers who don't yet have a reliability score
df = df[df['reliability_score'].notnull()]

idk_val = "I can't figure this one out."

# The values will be one in the case of raters' sharing 
# an identical reliability score... Or in the case of a rater 
# seeing the same image twice (and thus being seen as two different raters)
# Use this as a reference to give power back to raters not as proflific 
# if the ratio is high, trust the higher rater, but if the ratio's low,
# then two raters with similar reliabilities are asking to be looked at further
gb = (df.groupby('Image_ID')['reliability_score']
     .apply(rev_sorted)
     .apply(top_n_raters)
     .apply(rating_ratio))

# Master data list
data = []

# For each retired deed
for img_id, frame in df.groupby('Image_ID'):
    # Try to calculate the mode using the most-common-value current system...
    # This is just being done on one field, "Match"... Kevin, you'll have to
    # extend this to other fields, too.
    try:
        mode_val = mode(frame['Match'])
        
        # If most popular value is IDK, flag that record
        if mode_val == idk_val:
            idk_flag = True
        else:
            idk_flag = False
        
        # "No conflicts" meaning we were able to calc. mode
        no_conflicts = True

        # Store information for this image
        data.append({
            'img_id': img_id,
            'mode': mode_val,
            'idk_flag': idk_flag,
            'no_conflicts': no_conflicts
        })

    # a StatisticsError exception will be raised when
    # math.mode can't calculate mode 
    except StatisticsError:
        # Order the match choices based on rater reliability
        frame.sort_values('reliability_score',
                            ascending=False,
                            inplace=True)

        # Probably easiest to take the answer of the most reliable rater
        # This seems problematic, however, since Penny has seen every deed
        # and is the most reliable rater. Because of this issue,
        # we can track some other information below to make use
        # of the reliability scores
        mode_val = frame['Match'].values[0]

        # Track all of the answers, raters, and ranks
        # involved with a particular deed
        answers = frame['Match'].values.tolist()
        raters = frame['User_Name'].values.tolist()
        rater_ranks = frame['rank'].values.tolist()
        avg_rater_rank = np.mean(rater_ranks)

        top_rater = raters[0]

        # Ratio of the ranks between the top two raters
        top_two_ratio = gb.ix[img_id]

        row_data = {}

        if mode_val == idk_val:
            idk_flag = True
            next_best_data = iter_until(answers, rater_ranks)
            row_data = {**row_data, **next_best_data}
        else:
            idk_flag = False

        no_conflicts = False

        more_data = {
            'img_id': img_id,
            'top_answer': mode_val,
            'answers': answers,
            'raters': raters,
            'rater_ranks': rater_ranks,
            'top_rater': top_rater,
            'avg_rater_rank': avg_rater_rank,
            'top_two_ratio': top_two_ratio,
            'idk_flag': idk_flag,
            'no_conflicts': no_conflicts
        }
        
        row_data = {**row_data, **more_data}

        data.append(row_data)

frame = pd.DataFrame.from_records(data)

# Sort ascending by top_two_ratio
# the downside of this approach is that the reliability score
# is basically saying Penny's word is the truth every time
# 
# Checking out what some of the other raters (whose classifications
# are of a similar quality) might help shed more light on the issue
frame.sort_values('top_two_ratio', inplace=True)

# My suggestion would be to look at the deeds
# with small top_two_ratio values (meaning similar reliability between
# raters) and idx_flag == True (i.e. "IDK" being the top answer, but clearly
# not the only answer, since mode wasn't able to be calculated)
# If someone with a high rank says "IDK" but someone with a 
# similar rank says "yes", maybe you take the "yes" instead of manually
# reading the deed yourself...
print(frame[(frame['no_conflicts'] == False) & (frame['idk_flag'] == True)])