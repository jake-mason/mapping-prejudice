'''
Reliability score calculation script
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
should work with most versions of numpy, pandas,
and scikit-learn. It is highly recommended that 
you run Python >= 3.x and not Python 2.x.
'''

# If still running Python 2.x, need floating-point
# division, not integer division
import sys
if sys.version_info.major == 2:
    from __future__ import division

# Edit this path to point to the "Intermediate" folder
import os

import time

import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score

def handle_zero_division(x, y):
    try:
        return x/y
    except ZeroDivisionError:
        return None

os.chdir('/path/to/intermediate')

# Read a placeholder file
df = pd.read_csv('<PLACEHOLDER>.csv')

# Will need in order to sort by the most recent classification
df['Class_Date'] = pd.to_datetime(df['Class_Date'])

# In the case of a user having seen an image more than once,
# take their most recent answer.
df = (df.sort_values('Class_Date', ascending=False)
     .drop_duplicates(subset=['User_Name', 'Image_ID']))

# Master list which will store information
# calculated below
reliability_data = []

# Create groupby object to iterate through below
gb = df.groupby('User_Name')

# For each volunteer ("user" == "volunteer")
for user, user_df in gb:

    # Images the main volunteer has seen and associated ratings 
    user_img_seen = dict(zip(user_df['Image_ID'], user_df['Match']))   
    
    # Create another groupby object for every other volunteer
    other_gb = df[df['User_Name'] != user].groupby('User_Name')

    # For every other user... You will want to automatically filter out 
    # trolls/unreliable raters you find as you go along.. I think this is 
    # part of the cleaning script currently.
    for other_user, other_df in other_gb:

        # Images the other volunteer has seen and associated ratings
        other_user_img_seen = dict(zip(other_df['Image_ID'], other_df['Match']))
        
        # Set intersection between what the volunteer's 
        # seen and what the other volunteer has seen
        common = set(user_img_seen) & set(other_user_img_seen)

        # We only care to measure agreement between 
        # raters who have seen the same deeds
        if common:
            # Pairs of answers for each deed (image) commonly seen
            together = [(user_img_seen[img], other_user_img_seen[img])
                            for img in common]

            # Used to calculate Cohen's Kappa...
            # Just lists of each user's answers for all deeds shared
            user_vector = [x[0] for x in together]
            other_user_vector = [x[1] for x in together]
            
            # If cohen_kappa_score returns np.nan, then we know each user agreed 100%...
            # but there was no "random chance" component
            
            # https://github.com/scikit-learn/scikit-learn/issues/9624
            # "1 in Cohen's Kappa indicates perfect agreement 
            # with 0 chance of agreement at random.
            # Here there is perfect agreement at random."
            
            # Cohen's Kappa can also be zero when one rater 
            # gives the same answer for every subject
            # (e.g. in the case) of a "no" troll
            cohen_kappa = cohen_kappa_score(user_vector, other_user_vector)
                        
            # If we were able to calculate a kappa value
            if not np.isnan(cohen_kappa):

                # Sets of IDs agreed- and disagreed-upon
                agreements = {img for img in common 
                              if user_img_seen[img] == other_user_img_seen[img]}
                
                disagreements = {img for img in common 
                                 if user_img_seen[img] != other_user_img_seen[img]}
                
                # Number of images in common, agreed-upon, and disagreed-upon
                n_common = len(common)
                n_agreements = len(agreements)
                n_disagreements = len(disagreements)

				# Data to keep... JSON-style
                reliability_data.append(
                    {
                    'user': user,
                    'other_user': other_user,
                    'cohen_kappa': cohen_kappa,
                    'n_in_common': n_common,
                    'user_together_drop_dupe': frozenset((user, other_user)),

                    # The following are relatively more naive measures of reliability...
                    'n_agreements': n_agreements,
                    'n_disagreements': n_disagreements,
                    'perc_agreements': handle_zero_division(n_agreements, n_common),
                    'perc_disagreements': handle_zero_division(n_disagreements, n_common),
                    'agree_disagree_ratio': handle_zero_division(n_agreements, n_disagreements)
                    }
                )

# Create a dataframe out of the information collected above
agreement_df = pd.DataFrame.from_records(reliability_data)

# Obtain the average Kappa score for each user
# this is an average of the kappa between a given user and every user with whom
# they shared images and disagreed at least once
# Median is a bad measure, here, because of the usual skewness 
# of this distribution, so let's use mean
avg_kappa = agreement_df.groupby(['user'])['cohen_kappa'].mean()

# Number of classifications for each user
# this is used to develop the final reliability score later on
num_clfs = df.groupby(['User_Name']).size().to_frame('n_clfs')

# Put together the number of classifications and Cohen's Kappa values for each user
reliability_df = pd.concat((avg_kappa, num_clfs), axis=1)

# Product of each user's Cohen's Kappa score and the log of the number of classifications completed
# There are diminishing "returns" to an increasing number of shared images...
# The effect will always be positive, but incremental gains early on are much more rewarding than later on
reliability_df['reliability_score'] = reliability_df['cohen_kappa'] * np.log(reliability_df['n_clfs'])

# Rank the reliability scores. This isn't explicitly used, but might be valuable someday...
reliability_df['rank'] = reliability_df['reliability_score'].rank(ascending=False)

# Identify and flag raters in the
# bottom 20% in terms of reliability...
# could also look at bottom tail of distribution
# of reliability scores... raters significantly 
# (i.e. 1-2 stddevs) below "normal"
n_raters = reliability_df.shape[0]
perc = 0.2
cutoff = n_raters * (1-perc)
bottom_percent_ranks = {i for i in reliability_df['rank'] if i >= cutoff}

reliability_df['bottom_percent'] = np.where(reliability_df.isin(bottom_percent_ranks), True, False)

# Save the results with a unique (daily) identifier
session_id = "_".join(map(str, time.localtime()[:3]))
fname = 'reliability_scores_{}.csv'.format(session_id)

# Keep username as a column, obviously
reliability_df.reset_index(drop=False).to_csv(fname, index=False)