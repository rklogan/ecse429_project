import sys
import importlib
import threading
import generate_test_vectors
import numpy as np
import importlib
import sut

sut_filename = 'sut.py'
if(len(sys.argv) >= 2):
    filename = sys.argv[1]

mutant_list_filename = 'mutant_list.txt'

test_cases_filename = 'test_vectors.csv'

list_of_mutant_files = []
pooopooooopoooo

edge_cases = [" ", [2], [], "hello", "stuff", [], "&", "", [1], [10]]
num_cases = 100
test_cases = []
for i in range(num_cases):
    test_cases.append(generate_test_vectors.generate_vectors())

def generate_mutant_list():
    #open the software under test
    sut = open(sut_filename).readlines()

    #get the file extension for mutants
    file_extension = '.txt'

    mutant_number = 0 
    mutation_counts = [0,0,0,0]
    symbols = ['+','-','*','/']

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

def sequential_test():
    num_pass = 0
    for test in edge_cases:
        if compare_mutant_code(0, test):
            num_pass += 1
    for test in test_cases:
        if compare_mutant_code(0, test):
            num_pass += 1
    
    pass_pct = float(num_pass) / float(len(edge_cases) + len(test_cases)) * 100
    print(str(pass_pct) + " percent of mutants were killed.")

def parallel_test():
    num_threads = 3
    threads = []

    i = 0
    while i < len(edge_cases):
        #spawn thread with callback
        for j in range(num_threads):
            if i + j >= len(edge_cases):
                break
            t = threading.Thread(target=compare_mutant_code, args = (0,), kwargs={"test_vector":edge_cases[i+j]})
            threads.append(t)
            t.start()

        #wait for threads to finish
        for t in threads:
            t.join()
            
        i += j


    i = 0
    while i < len(test_cases):
        #spawn thread with callback
        for j in range(num_threads):
            if i + j >= len(test_cases):
                break
            
            t = threading.Thread(target=compare_mutant_code, args = (0,), kwargs={"test_vector":test_cases})
            threads.append(t)
            t.start()

        #wait for threads to finish
        for t in threads:
            t.join()
        i += j

def compare_mutant_code(num,test_vector):
    mutant_was_killed = False
    for file in list_of_mutant_files:
        file = file.split('.')[0]
        mutant_file = importlib.import_module(file)
        try:
            correct_result = sut.standard_deviation(test_vector)
        except Exception as e1:
            try:
                mutant_result = mutant_file.standard_deviation(test_vector)
            except Exception as e2:
                print('double exception')
                print(test_vector)
                print()
                #pass
                #return (type(e1) is type(e2) and e1.args == e2.args)
        else:
            try:
                mutant_result = mutant_file.standard_deviation(test_vector)
            except:
                if(num == 0):
                    with open(mutant_list_filename, 'a+') as mutant_file:
                        mutant_file.write(file + " was killed " '\n')
                    mutant_was_killed = True
            
            if(abs(correct_result - mutant_result) > 0.0000001):
                if(num == 0):
                    with open(mutant_list_filename, 'a+') as mutant_file:
                        mutant_file.write(file + " was killed " '\n')
                mutant_was_killed = True
            else:
                print('equal')
                print(correct_result)
                print(mutant_result)
                print(test_vector)
                print(file)
                print()
    return mutant_was_killed


generate_mutant_list()
generate_mutated_code()

compare_mutant_code(0, [40, 31, 54, 75, 11, -9, 20, 53.73])
#sequential_test()
#parallel_test()
