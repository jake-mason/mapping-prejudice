import pandas as pd

# Raw extract from Google Sheets
df = pd.read_excel('/Users/jake/Downloads/Mapping Prejudice Inter-rater Reliability (Responses).xlsx')

# Every deed classification field
columns = [c for c in df if 'deed' in c.lower()]

# Treat timestamp as unique user ID -- should
# be granular enough so as not to cause conflicts
melted = pd.melt(df, 'Timestamp', columns)

# Sort by user
melted.sort_values('Timestamp', inplace=True)