import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Read the CSV file into a DataFrame
df = pd.read_csv('statistical_results.txt')

# Display the first 5 rows
print(df.head().to_markdown(index=False, numalign="left", stralign="left"))

# Print the column names and their data types
print(df.info())

# Split the `name` column into two columns `name` and `test_size`
df[['name', 'test_size']] = df['name'].str.split('-', expand=True)

# Convert `test_size` column to numeric
df['test_size'] = pd.to_numeric(df['test_size'])

# Group the dataframe by `name` and calculate the mean of `mean` column
df_grouped = df.groupby(['name', 'test_size'])[' mean'].mean().reset_index()

# Get unique names
unique_names = df_grouped['name'].unique()

# Create subplots
fig, axes = plt.subplots(nrows=len(unique_names), ncols=1, figsize=(10, 30))

# Iterate and plot
for i, name in enumerate(unique_names):
    df_subset = df_grouped[df_grouped['name'] == name]
    axes[i].plot(df_subset['test_size'], df_subset[' min'])
    axes[i].set_xlabel('Test Size')
    axes[i].set_ylabel('Average Mean')
    axes[i].set_title(f'Average Mean vs Test Size for {name}')

# Adjust layout
plt.tight_layout()

# Show the plot
plt.show()
print(df_grouped.to_markdown(index=False))