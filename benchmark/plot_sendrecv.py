import pandas as pd
import matplotlib.pyplot as plt
import sys

# Get the input file names from the command line arguments
input_files = sys.argv[1:]

# Create an empty list to store the data from all files
all_data = []

# Iterate over the input files
for file in input_files:
    # Load the data from the text file into a Pandas DataFrame
    df = pd.read_csv(file)

    # Extract the size from the `name` column
    df['size'] = df['name'].str.split('-').str[1].astype(int)

    # Split the `name` column by the '-' delimiter
    df['test_name'] = df['name'].str.split('-').str[0]

    # Append the DataFrame to the list
    all_data.append(df)

# Concatenate all the DataFrames into a single DataFrame
df = pd.concat(all_data)

# Set the `test_name` column as the index
df = df.set_index('test_name')

# Remove any trailing and leading spaces from all column names
df.columns = df.columns.str.strip()

# Unstack the DataFrame to have `size` as the row index and `test_name` as the column index
df_unstacked = df.groupby(['size', 'test_name'])['min'].min().unstack()
print(df_unstacked)
# Create a line plot with `size` on the x-axis and `min` on the y-axis
df_unstacked.plot(kind='line', marker='o')

# Set the title of the plot
plt.title('Minimum Time by Size')

# Set the x and y labels
plt.xlabel('Size (bytes)')
plt.ylabel('Minimum Time (s)')

# Add a legend
plt.legend()
plt.grid(True)

# Display the plot
plt.show()