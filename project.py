import sys
import importlib
import threading
import generate_test_vectors
import numpy as np
import importlib
import sut
import time
import tokenize
import io

#get CLAs
sut_filename = 'sut.py'
sut_no_comment_filename = 'no_comment.py'
num_threads = 3
if(len(sys.argv) >= 2):
    num_threads = int(sys.argv[1])
if(len(sys.argv) >= 3):
    filename = sys.argv[2]

mutant_list_filename = 'mutant_list.txt'
test_cases_filename = 'test_vectors.csv'
list_of_mutant_files = []
dead_mutants = []

#generate test data
edge_cases = [" ", [2], [], "hello", "stuff", [], "&", "", [1], [10]]
num_cases = 100
test_cases = []
for i in range(num_cases):
    test_cases.append(generate_test_vectors.generate_vectors())


#function that generate all the mutants of the sut
def generate_mutant_list():
    #open the software under test
    sut = open(sut_filename).readlines()

    #get the file extension for mutants
    file_extension = '.txt'

    mutant_number = 0 
    mutation_counts = [0,0,0,0]
    symbols = ['+','-','*','/']
    in_multiline = False

    with open(mutant_list_filename, 'w+') as mutant_file:
        #iterate over each line
        for i in range(len(sut)):
            line = sut[i]

            #iterate over each character on the line
            for j in range(len(line)):
                prev = ''.join(line[0:j])

                # if we find arithmetic, generate mutants
                if line[j] in symbols:

                    #check each of the possible operations
                    for k in range(4):
                        #if the symbols is the same as the original it's not a mutant
                        if(line[j] == symbols[k]): continue

                        #make sure the line terminates with a line break
                        if '\n' not in line: line += '\n'

                        #generate the mutant line
                        mutant = line[0:j] + symbols[k] + line[j+1:]

                        #write the data to file
                        mutant_file.write("Mutant " + str(mutant_number) + " On Line " + str(i) + '\n')
                        mutant_file.write("Originally: " + str(line))
                        mutant_file.write("Mutant: " + mutant)
                        mutant_file.write("Type: " + symbols[k] + '\n\n')

                        #increment the counters
                        mutant_number += 1
                        mutation_counts[k] += 1
        
        #write the totals for the mutants
        for i in range(4):
            mutant_file.write('Number of \'' + symbols[i] +'\' mutations: ' + str(mutation_counts[i]) + '\n')

#converts a list of mutants into python scripts
def generate_mutated_code():
    #some constants used to trim mutant list entries
    chars_to_split_line_2 = len('Originally: ')
    chars_to_split_line_3 = len('Mutant: ')
    chars_to_split_line_4 = len('Type: ')

    #get the filenames
    sut_file_extension = sut_filename.split('.')[1]

    #parse the mutant list file
    with open(mutant_list_filename) as ml_file:
        #initialize the entry
        mutant_number = -1
        mutant_line_number = -1
        originally = ""
        mutant = ""
        mutation_type = ""
        lines_of_entry_parsed = 0
        
        for ml_line in ml_file:
            #check which line of the entry we are on. Entries are 5 lines
            if 'On Line' in ml_line and lines_of_entry_parsed == 0:
                #first line of the entry
                tokens = ml_line.split(' ')
                mutant_number = int(tokens[1])
                mutant_line_number = int(tokens[4])
                lines_of_entry_parsed += 1
            elif 'Originally: ' in ml_line and lines_of_entry_parsed == 1:
                originally = ml_line[chars_to_split_line_2:]
                lines_of_entry_parsed += 1
            elif 'Mutant: ' in ml_line and lines_of_entry_parsed == 2:
                mutant = ml_line[chars_to_split_line_3:]
                lines_of_entry_parsed += 1
            elif 'Type: ' in ml_line and lines_of_entry_parsed == 3:
                mutation_type = ml_line[chars_to_split_line_4:]
                lines_of_entry_parsed += 1
            elif ml_line == '\n' and lines_of_entry_parsed == 4:
                #we have a complete entry
                output_filename = 'Mutation ' + str(mutant_number)
                output_filename += '.' + sut_file_extension
                list_of_mutant_files.append(output_filename)

                with open(sut_filename) as sut, open(output_filename, 'w+') as output_file:
                    if mutant_line_number != 0:
                        #write the lines that come before the mutant to the output file
                        header = [next(sut) for i in range(mutant_line_number)]
                        #if mutant_line_number == 10: print(header)
                        #for line in header:
                        output_file.writelines(header)
                    
                    #write the mutant
                    output_file.write(mutant)
                    next(sut)

                    #copy the rest of the file
                    for line in sut:
                        output_file.write(line)

                #prepare to process another entry         
                mutant_number = -1
                mutant_line_number = -1
                originally = ""
                mutant = ""
                mutation_type = ""
                lines_of_entry_parsed = 0

            elif 'Number of' in ml_line:
                #we have reached the footer
                print('Processing Complete')
                break
            else:
                #the current mutant is malformed. reset the values and continue searching
                print('Malformed mutant entry detected')
                print(ml_line)
                mutant_number = -1
                mutant_line_number = -1
                originally = ""
                mutant = ""
                mutation_type = ""
                lines_of_entry_parsed = 0

#returns true if the given mutant object is killed by the vector
def attempt_to_kill(mutant, vector):
    #check exception cases
    correct_threw = False
    mutant_threw = False
    try:
        sut.standard_deviation(vector)
    except Exception:
        correct_threw = True

    try:
        mutant.standard_deviation(vector)
    except Exception:
        mutant_threw = True

    if(correct_threw and mutant_threw):
        return False
    elif(correct_threw != mutant_threw):
        return True
    else:
        #otherwise compute the output
        correct = sut.standard_deviation(vector)
        mutant_value = mutant.standard_deviation(vector)
        if(correct == mutant_value):
            return False
        return True

#function to remove comments from sur
def remove_comments(sut_filename='sut.py'):
    #load the file into a string
    string = ''
    with open(sut_filename) as sut:
        for line in sut:
            string += line

    #create a buffer
    buf = io.StringIO(string)

    output_tokens = []
    
    #tokenize and process
    for token in tokenize.generate_tokens(buf.readline):
        #remove single line comments
        if token.type == tokenize.COMMENT:
            continue
        #skip multiline comments
        elif token.type == tokenize.STRING:
            if token.string[0:3] == "'''" or token.string[0:3] == '"""':
                continue

        output_tokens.append(token)

    with open(sut_no_comment_filename, 'w+') as snc:
        snc.write(tokenize.untokenize(output_tokens))

    return sut_no_comment_filename

#this functions tests all the test vectors on the given mutant
def test_mutant(num, mutant_filename):
    mutant_name = mutant_filename.split('.')[0]
    mutant = importlib.import_module(mutant_name)

    #run the tests
    killers = []
    for vector in edge_cases:
        if attempt_to_kill(mutant, vector):
            killers.append(vector)

    for vector in test_cases:
        if attempt_to_kill(mutant, vector):
            killers.append(vector)

    #output the data
    with open(mutant_list_filename, 'a+') as mutant_file:
        if killers != []:
            for killer in killers:
                mutant_file.write(mutant_name + ' was killed by: ' + str(killer) + '\n')
        else:
            mutant_file.write(mutant_name + ' was not killed.')
        print(mutant_name + ' was killed by: ' + str(len(killers)) + ' vectors')
    
    #add the mutant to the list in RAM
    if(len(killers) > 0):
        dead_mutants.append(mutant_name)    

#test every mutant sequentially
def sequential_test():
    dead_mutants = []
    for mutant_file in list_of_mutant_files:
        test_mutant(0, mutant_file)

#test in parallel
def parallel_test():
    dead_mutants = []

    i = 0
    threads = []
    while i < len(list_of_mutant_files):
        for j in range(num_threads):
            if i+j >= len(list_of_mutant_files):
                break
            t = threading.Thread(target=test_mutant, args=(1,), kwargs={'mutant_filename':list_of_mutant_files[i+j]})
            threads.append(t)
            t.start()

        for k in threads:
            k.join()
        i += num_threads

sut_filename = remove_comments(sut_filename)
generate_mutant_list()
generate_mutated_code()

start = time.time()
if num_threads == 1:
    sequential_test()
else:
    parallel_test()
elapsed = time.time() - start

#calculate coverage
coverage = float(len(dead_mutants)) / float(len(list_of_mutant_files)) * 100
print(str(coverage) + '% Mutant Coverage')
print("Executed in: " + str(elapsed) + 's')
open(mutant_list_filename, 'a+').write(str(coverage) + '% Mutant Coverage')