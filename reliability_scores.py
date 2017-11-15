import os
os.chdir('/path/to/intermediate')

import time

import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score

def handle_zero_division(x, y):
    try:
        return x/y
    except ZeroDivisionError:
        return None
        
# This read a placeholder file
df = pd.read_csv('<PLACEHOLDER>.csv')

# Sort to order by the most recent classification
df.sort_values('Class_Date', ascending=False, inplace=True)
# In the case of a user having seen an image more than once,
# take their most recent answer (this is where the sorting from
# above comes into play)
df.drop_duplicates(subset=['User_Name', 'Image_ID'], inplace=True)

# Master list which will store JSON, basically
reliability_data = []

for user, user_df in df.groupby('User_Name'):
    # Images the main user has seen and associated ratings 
    user_img_seen = dict(zip(user_df['Image_ID'], user_df['Match']))   
    
    for other_user, other_df in df[df['User_Name'] != user].groupby('User_Name'):
        # Images the other user has seen and associated ratings
        other_user_img_seen = dict(zip(other_df['Image_ID'], other_df['Match']))
        
        # Set intersection between what the user's seen and what the other user has seen
        common = set(user_img_seen) & set(other_user_img_seen)

        # We only care to measure agreement between raters who have seen the same deeds
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

				# Data to keep
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
# Median might be valuable to look at, too, depending on skewness
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

# Save the results
session_id = "_".join(map(str, time.localtime()[:3]))
fname = 'reliability_scores_{}.csv'.format(session_id)

reliability_df.reset_index().to_csv(fname, index=False)
