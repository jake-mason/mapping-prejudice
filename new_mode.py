import os
os.chdir('/Users/jake/Documents/stareightytwo/projects/mapping_prejudice/assets/data')

import pandas as pd
import numpy as np
from statistics import mode, StatisticsError

# Read in "placeholder" file
df = pd.read_excel('mp_data.xlsx')

# Ignore images already retired
df = df[df['Retired'] != 'Retired']

# Read in rater reliability ratings
ratings_df = pd.read_csv('user_ratings.csv')

# Join each rater's agreement index score with each image they've seen (each row)
df = pd.merge(df, ratings_df,
            left_on='User_Name',
            right_on='index',
            how='left')

# Average rater score for each image
gb = df.groupby('Image_ID')['reliability_score'].agg(['count', 'mean']).reset_index()

data = []

for img_id, frame in df.groupby('Image_ID'):
    try:
        most_popular_value = mode(frame['Match'])
    except StatisticsError:
        # Order the match choices based on rater reliability
        frame.sort_values('reliability_score',
                            ascending=False,
                            inplace=True)

        # Probably easiest to take the answer of the most reliable rater
        top_answer = frame['Match'].values[0]

        answers = frame['Match'].values.tolist()
        raters = frame['User_Name'].values.tolist()
        rater_ranks = frame['rank'].values.tolist()
        avg_rater_rank = np.mean(rater_ranks)

        top_rater = raters[0]

        data.append(
            {
            'img_id': img_id,
            'top_answer': top_answer,
            'answers': answers,
            'raters': raters,
            'rater_ranks': rater_ranks,
            'top_rater': top_rater,
            'avg_rater_rank': avg_rater_rank
            }
        )