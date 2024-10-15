import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Read the CSV file into a DataFrame
df = pd.read_csv(' results/jetstream/statistical_results.txt')

# Display the first 5 rows
print(df.head().to_markdown(index=False, numalign="left", stralign="left"))

# Print the column names and their data types
print(df.info())

# Split the `name` column into two columns `name` and `test_size`
df[['name', 'test_size']] = df['name'].str.split('-', expand=True)

# Convert `test_size` column to numeric
df['test_size'] = pd.to_numeric(df['test_size'])

# Group the dataframe by `name` and calculate the mean of `mean` column
df_grouped = df.groupby(['name', 'test_size'])[' min'].mean().reset_index()

# Get unique names
unique_names = df_grouped['name'].unique()

# Create subplots
fig, axes = plt.subplots(nrows=len(unique_names)//2, ncols=2, figsize=(30, 20), sharex=True, sharey=True, layout="constrained")

# Iterate and plot
for i, name in enumerate(unique_names):
    df_subset = df_grouped[df_grouped['name'] == name]
    print("------------------------------------------")
    print(df_subset)
    axes[i//2][i%2].plot(df_subset['test_size'], df_subset[' min'])
    axes[i//2][i%2].set_xlabel('Test Size')
    axes[i//2][i%2].set_ylabel('Average Mean')
    axes[i//2][i%2].set_title(f'Average Mean vs Test Size for {name}')
    axes[i//2][i%2].set_xscale('log')

# Adjust layout
plt.tight_layout()

# Show the plot
plt.show()
print(df_grouped.to_markdown(index=False))