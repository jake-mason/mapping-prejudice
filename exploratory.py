import os
os.chdir('/Users/jake/Documents/stareightytwo/projects/mapping_prejudice/mapping_prejudice/Intermediate')

from collections import Counter
from itertools import combinations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('placeholder_10_8_2017.csv')
df.replace({'null': np.nan}, inplace=True)

df['Class_Date'] = pd.to_datetime(pd.to_datetime(df['Class_Date']).astype(str).str.split().str[0])


df.groupby(['Class_Date']).size().plot(title='Number of classifications over time')

overlap = {}

n_users = len(set(df['User_Name']))

for user, user_df in df.groupby('User_Name'):
    overlap[user] = {}
    user_img_seen = set(user_df['Image_ID'])

    for other_user, other_df in df[df['User_Name'] != user].groupby('User_Name'):
        other_user_img_seen = set(other_df['Image_ID'])

        common = user_img_seen & other_user_img_seen
        
        overlap[user][other_user] = {'common': common,
                                    'number': len(common)}

    n_users -= 1

    if n_users % 20 == 0:
        print('{} users left'.format(n_users))

# Should be 5562
numbers = [overlap[user][other_user]['number'] for user in overlap for other_user in overlap[user]]

sum(1 for n in numbers if n > 0)

Counter(numbers).most_common()[:20]

# All users have at least one overlap
anything_for_user = [1 if any(overlap[user][other_user]['number'] > 0 for other_user in overlap[user]) else 0 for user in overlap]

# Number of overlaps per user
n_overlaps_by_user = {user: sum(overlap[user][other_user]['number'] for other_user in overlap[user]) for user in overlap}

Counter([v for k, v in n_overlaps_by_user.items()]).most_common()[:20]

n_overlaps_sorted = sorted([v for k, v in n_overlaps_by_user.items()], reverse=True)