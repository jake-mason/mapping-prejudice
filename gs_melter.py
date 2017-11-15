import pandas as pd
import re

# Raw extract from Google Sheets
df = pd.read_excel('/Users/jake/Downloads/Mapping Prejudice Inter-rater Reliability (Responses).xlsx')

# Every deed classification field
columns = [c for c in df if 'deed' in c.lower()]
columns_numbers = {re.search('\d+', c).group(): c for c in columns}

# Source-of-truth mapping
#sot_mapping_deprec = [{'1991_0351_match.jpg': [('deed_0.jpg', '0'), ('deed_22.jpg', '22')]},
#                {'948_0535_match.jpg': [('deed_1.jpg', '1'), ('deed_19.jpg', '19')]},
#                {'1647_0406_match.jpg': [('deed_2.jpg', '2'), ('deed_4.jpg', '4')]},
#                {'1492_0072_match.jpg': [('deed_3.jpg', '3'), ('deed_25.jpg', '25')]},
#                {'1237_0160_match.jpg': [('deed_5.jpg', '5'), ('deed_13.jpg', '13')]},
#                {'1350_0564_match.jpg': [('deed_6.jpg', '6'), ('deed_26.jpg', '26')]},
#                {'1223_0233_match.jpg': [('deed_7.jpg', '7'), ('deed_17.jpg', '17')]},
#                {'2623_0575_match.jpg': [('deed_8.jpg', '8'), ('deed_20.jpg', '20')]},
#                {'2227_0302_match.jpg': [('deed_9.jpg', '9'), ('deed_27.jpg', '27')]},
#                {'967_0231_match.jpg': [('deed_10.jpg', '10'), ('deed_23.jpg', '23')]},
#                {'1634_0420_match.jpg': [('deed_11.jpg', '11'), ('deed_28.jpg', '28')]},
#                {'1759_0284_match.jpg': [('deed_12.jpg', '12'), ('deed_24.jpg', '24')]},
#                {'1122_0227_match.jpg': [('deed_14.jpg', '14'), ('deed_18.jpg', '18')]},
#                {'1447_0415_match.jpg': [('deed_15.jpg', '15'), ('deed_29.jpg', '29')]},
#                {'831_0346_match.jpg': [('deed_16.jpg', '16'), ('deed_21.jpg', '21')]}]

# Map obfuscated deed IDs to actual deed IDs... Each actual
# deed repeated twice
sot_mapping = {'1': '1991_0351_match.jpg',
                '10': '2227_0302_match.jpg',
                '11': '967_0231_match.jpg',
                '12': '1634_0420_match.jpg',
                '13': '1759_0284_match.jpg',
                '14': '1237_0160_match.jpg',
                '15': '1122_0227_match.jpg',
                '16': '1447_0415_match.jpg',
                '17': '831_0346_match.jpg',
                '18': '1223_0233_match.jpg',
                '19': '1122_0227_match.jpg',
                '2': '948_0535_match.jpg',
                '20': '948_0535_match.jpg',
                '21': '2623_0575_match.jpg',
                '22': '831_0346_match.jpg',
                '23': '1991_0351_match.jpg',
                '24': '967_0231_match.jpg',
                '25': '1759_0284_match.jpg',
                '26': '1492_0072_match.jpg',
                '27': '1350_0564_match.jpg',
                '28': '2227_0302_match.jpg',
                '29': '1634_0420_match.jpg',
                '3': '1647_0406_match.jpg',
                '30': '1447_0415_match.jpg',
                '4': '1492_0072_match.jpg',
                '5': '1647_0406_match.jpg',
                '6': '1237_0160_match.jpg',
                '7': '1350_0564_match.jpg',
                '8': '1223_0233_match.jpg',
                '9': '2623_0575_match.jpg'}

new_deed_columns = {columns_numbers[k]: re.search('\d+', k).group()
                    for k in columns_numbers}

df.rename(columns=new_deed_columns, inplace=True)

imgs = set(sot_mapping.values())
# Kevin E-S's expert ratings for all 15 deeds
expert_answers = {'1122_0227_match.jpg': 'No',
                '1223_0233_match.jpg': 'Yes',
                '1237_0160_match.jpg': 'Yes',
                '1350_0564_match.jpg': 'No',
                '1447_0415_match.jpg': 'No',
                '1492_0072_match.jpg': 'Yes',
                '1634_0420_match.jpg': 'Yes',
                '1647_0406_match.jpg': 'No',
                '1759_0284_match.jpg': 'Yes',
                '1991_0351_match.jpg': 'No',
                '2227_0302_match.jpg': 'No',
                '2623_0575_match.jpg': 'No',
                '831_0346_match.jpg': 'Yes',
                '948_0535_match.jpg': 'Yes',
                '967_0231_match.jpg': 'Yes'}

# Create columns to match what Kevin needs
rater_ratings = []
for rater, frame in df.groupby('Nickname (optional)'):
    for img_col in sot_mapping:
        data = {
            'appraisers': rater,
            'vol_rating': frame[img_col].values[0],
            'sample': img_col 
        }
        rater_ratings.append(data)

rater_ratings = pd.DataFrame.from_records(rater_ratings)
rater_ratings['sample_mapping'] = rater_ratings['sample'].map(sot_mapping)
rater_ratings['sample'] = rater_ratings['sample'].astype(int)
rater_ratings.sort_values(['sample', 'appraisers'],
                          ascending=True,
                          inplace=True)
rater_ratings.reset_index(inplace=True, drop=True)
                        
stdorder, runorder = ([x+1 for x in rater_ratings.index],)*2

rater_ratings['stdorder'] = stdorder
rater_ratings['runorder'] = runorder
rater_ratings['expert_rating'] = rater_ratings['sample_mapping'].map(expert_answers)

# Write to file
melted.to_csv('/Users/jake/Downloads/mp_responses.csv', index=False)