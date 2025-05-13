import matplotlib.pyplot as plt

# --------------------------------------------------------------------
# 1) Define the data
# --------------------------------------------------------------------
boys_data = [1, 1, 1, 2, 2, 2.5, 3, 3, 3, 4, 10]
girls_data = [1, 1, 1.5, 2, 3.5, 4, 4, 4, 5, 6, 12, 14]

# --------------------------------------------------------------------
# 2) Helpers to compute median + classical 5-number summary
# --------------------------------------------------------------------
def median_of_sorted(values):
    """Median of a sorted list, using straightforward approach."""
    n = len(values)
    mid = n // 2
    if n % 2 == 1:
        # odd length
        return values[mid]
    else:
        # even length
        return (values[mid - 1] + values[mid]) / 2

def five_number_summary_classical(data):
    """
    Compute (Min, Q1, Median, Q3, Max) via classical 'by-hand' splitting:
      - Sort data.
      - If n is odd, exclude the middle from each half for Q1 and Q3.
      - If n is even, split exactly in half and take medians.
    """
    sorted_data = sorted(data)
    n = len(sorted_data)

    minimum = sorted_data[0]
    maximum = sorted_data[-1]

    # Median
    if n % 2 == 1:
        # odd length
        med_index = n // 2
        median_val = sorted_data[med_index]
        lower_half = sorted_data[:med_index]        # everything before the median
        upper_half = sorted_data[med_index+1:]      # everything after
    else:
        # even length
        mid1 = (n // 2) - 1
        mid2 = (n // 2)
        median_val = (sorted_data[mid1] + sorted_data[mid2]) / 2
        lower_half = sorted_data[:n//2]
        upper_half = sorted_data[n//2:]

    # Q1 = median of lower half
    q1 = median_of_sorted(lower_half) if len(lower_half) > 0 else None
    # Q3 = median of upper half
    q3 = median_of_sorted(upper_half) if len(upper_half) > 0 else None

    return (minimum, q1, median_val, q3, maximum)

# --------------------------------------------------------------------
# 3) Compute the 5-number summaries
# --------------------------------------------------------------------
b_min, b_q1, b_median, b_q3, b_max = five_number_summary_classical(boys_data)
g_min, g_q1, g_median, g_q3, g_max = five_number_summary_classical(girls_data)

# Print them out to confirm
print("Boys' Data (sorted):", sorted(boys_data))
print(f"  Min = {b_min}, Q1 = {b_q1}, Median = {b_median}, Q3 = {b_q3}, Max = {b_max}")
print()
print("Girls' Data (sorted):", sorted(girls_data))
print(f"  Min = {g_min}, Q1 = {g_q1}, Median = {g_median}, Q3 = {g_q3}, Max = {g_max}")

# --------------------------------------------------------------------
# 4) Make a single figure with two horizontal box plots side by side
# --------------------------------------------------------------------
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 4))

# -- Left subplot: Boys
ax_boys = axes[0]
ax_boys.boxplot(boys_data, vert=False)
ax_boys.set_title("Boys' Screen Time (Hours)")
ax_boys.set_xlabel("Hours")
ax_boys.set_xlim(0, 15)

# Mark the 5-number summary lines
ax_boys.axvline(b_min, color='black', linestyle='--', label=f'Min = {b_min}')
ax_boys.axvline(b_q1, color='green', linestyle='--', label=f'Q1 = {b_q1}')
ax_boys.axvline(b_median, color='red', linestyle='--', label=f'Median = {b_median}')
ax_boys.axvline(b_q3, color='blue', linestyle='--', label=f'Q3 = {b_q3}')
ax_boys.axvline(b_max, color='purple', linestyle='--', label=f'Max = {b_max}')
ax_boys.legend(loc='lower right')

# -- Right subplot: Girls
ax_girls = axes[1]
ax_girls.boxplot(girls_data, vert=False)
ax_girls.set_title("Girls' Screen Time (Hours)")
ax_girls.set_xlabel("Hours")
ax_girls.set_xlim(0, 15)

ax_girls.axvline(g_min, color='black', linestyle='--', label=f'Min = {g_min}')
ax_girls.axvline(g_q1, color='green', linestyle='--', label=f'Q1 = {g_q1}')
ax_girls.axvline(g_median, color='red', linestyle='--', label=f'Median = {g_median}')
ax_girls.axvline(g_q3, color='blue', linestyle='--', label=f'Q3 = {g_q3}')
ax_girls.axvline(g_max, color='purple', linestyle='--', label=f'Max = {g_max}')
ax_girls.legend(loc='lower right')

plt.tight_layout()
plt.show()
