def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers) #  Potential ZeroDivisionError if list is empty

data = []
print(f"Average: {calculate_average(data)}")
