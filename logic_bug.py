def calculate_average(numbers):
    total = 0
    # BUG: Off-by-one error in loop range, misses the last element
    for i in range(len(numbers) - 1):
        total += numbers[i]
    
    # BUG: Potential division by zero if list is empty
    return total / len(numbers)

def find_item(items, target):
    i = 0
    # BUG: Infinite loop if target is not in items
    while i < len(items):
        if items[i] == target:
            return i
        # Forgot to increment i implies infinite loop
    return -1
