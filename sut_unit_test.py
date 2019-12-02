import random
import statistics as stats
import math

def validate():
    for i in range(100):
        numbers = random.sample(range(i), random.randint(0, i))

        if numbers == []:
            try:
                standard_deviation(numbers)
            except:
                print("Test passed for []")
        elif len(numbers) == 1:
            print("Test " + str(i) + " skipped")
        elif (abs(standard_deviation(numbers) - stats.stdev(numbers)) < 0.00001):
            print("Test " + str(i) + " Passed")
        else:
            print(str(standard_deviation(numbers)) + " " + str(stats.stdev(numbers)))
            print("Test " + str(i) + " Failed")

validate()