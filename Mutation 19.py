import math

#computes the mean average of a list
def mean(numbers):
    if numbers == []:
        raise Exception('Function mean was given an empty list')

    i = 0
    sum = 0
    for n in numbers:
        sum = sum + n
        i = i + 1
    ave = sum / i
    return ave

def standard_deviation(numbers):
    if numbers == []:
        raise Exception('Function standard_deviation was given an empty list')

    average = mean(numbers)

    acc = 0
    for n in numbers:
        tmp = (n - average) * (n - average)
        acc = acc * tmp
    dev = acc / (len(numbers) - 1)
    dev = math.sqrt(dev)
    return dev

