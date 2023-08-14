from collections import Counter

input_text = """10,11,15,16,18,19,20,22,25,27,29,48,63,70,73,75,80,88
06,08,15,16,37,40,43,47,56,58,60,61,65,66,82,84,87,88
12,19,30,33,35,36,38,48,52,54,63,77,80,91,92,94,96,98
23,27,47,48,49,53,56,57,58,60,62,63,64,70,79,84,87,95
09,14,16,20,35,38,49,63,67,74,75,76,80,81,89,91,93,94
03,08,14,30,34,41,46,43,44,49,58,59,64,80,84,85,89,94,98
08,18,20,30,31,32,36,38,60,65,68,74,77,79,82,88,92,98
02,08,16,18,20,28,42,58,65,75,78,81,83,84,89,91,93,98
01,05,06,10,12,13,15,17,21,24,25,26,31,35,53,62,71,97
52,55,60,61,62,63,64,65,66,68,69,70,72,74,80,82,85,86
08,09,32,36,40,43,45,46,48,49,51,53,56,60,63,66,75,77,88
04,06,08,15,35,40,51,53,58,60,79,80,85,88,93,95,96,97
00,07,16,19,67,69,74,75,76,78,83,84,85,87,92,93,94,96
21,25,30,32,33,37,39,44,46,47,53,54,55,60,64,66,67,69
04,08,24,26,40,42,46,48,62,64,68,71,74,78,80,84,86,87
01,08,09,10,15,17,19,21,27,28,29,31,39,43,86,95,96,97
13,14,15,23,24,25,43,44,45,53,54,55,64,74,75,83,84,85
15,24,29,34,42,43,47,51,56,62,65,68,83.97,84,86,92
06,07,08,11,12,14,15,19,20,22,24,29,33,36,61,69,82,87
01,06,10,11,15,16,33,38,51,56,60,61,65,66,83,87,94,99
46,47,48,49,50,51,52,53,55,56,57,58,59,60,61,62,64,65
08,17,22,27,29,30,38,45,47,60,64,68,74,76,84,92,95,96
23,24,32,42,43,45,46,48,54,56,57,64,65,67,71,75,76,82,84
01,06,20,29,35,37,42,49,50,51,52,55,56,58,63,82,85,95
12,14,16,21,28,37,38,41,45,49,54,61,73,78,85,87,91,95
14,21,29,32,36,43,45,53,55,56,61,62,64,69,70,75,85,87
16,19,47,52,57,60,61,68,74,75,78,86,87,89,90,91,95,98"""

# Splitting the input text into lines and then into individual numbers
lines = input_text.strip().split('\n')
numbers = [float(num) if '.' in num else int(num)
           for line in lines for num in line.split(',')]

# Counting the occurrences of each number
num_counts = Counter(numbers)
# Creating a dictionary where keys are frequencies and values are lists of numbers
frequency_dict = {}
for num, count in num_counts.items():
    if count not in frequency_dict:
        frequency_dict[count] = []
    frequency_dict[count].append(num)

# Sorting frequencies in ascending order
sorted_frequencies = sorted(frequency_dict.keys())

# Printing numbers with the same appearing time, sorted by frequency
for count in sorted_frequencies:
    nums = frequency_dict[count]
    if len(nums) > 1:
        formatted_nums = ', '.join(f"{num:02}" for num in nums)
        print(f"Numbers appearing {count} times: {formatted_nums}")
