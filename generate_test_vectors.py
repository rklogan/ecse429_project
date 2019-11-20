import random


def generate_vectors():
    random_range = random.randint(0,10)
    out = random.sample(range(-100, 100), random_range)
    out.append(round(random.uniform(-100,100), 2))

    print(out)


generate_vectors()