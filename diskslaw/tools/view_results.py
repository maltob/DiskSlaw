#!/usr/bin/env python3

##
#
#  A quickly thrown together csv viewer for diskslaw to view the results
#
##

import sys
import os
import csv

PADDING = 2
MAX_LENGTH = 30
include_columns = ()
#Verify we have 2 arguments
if len(sys.argv) < 2:
    print ("There need to be two arguments.\nview_results <file> [max_column_length]")
    exit

# The third argument is max column length
if len(sys.argv) > 2:
    try:
        mlength = int(sys.argv[2])
        if mlength < 255:
            MAX_LENGTH = mlength
    except:
        print (sys.argv[2]+" is not a number")
    exit

# The fourth argument is list of columns
if len(sys.argv) > 3:
    try:
        include_columns = str(sys.argv[3]).split(",")
    except:
        print (sys.argv[3]+" is not a list")
    exit

#Verify one argument exists
if not os.path.exists(sys.argv[1]) :
    print ("The file "+sys.argv[1]+" does not exist")
    exit

arg_length = {}
with open(sys.argv[1],'r') as input_file:
    csv_reader = csv.DictReader(input_file, delimiter="\t")
    #Get the longest column
    for row in csv_reader:
        for fname in csv_reader.fieldnames:
            if fname in arg_length:
                if len(str(row[fname])) > arg_length[fname]:
                    arg_length[fname] = len(str(row[fname]))
            else:
                arg_length[fname] =len(fname)
                if len(str(row[fname])) > arg_length[fname]:
                    arg_length[fname] = len(str(row[fname]))
    #Show the headers
    for fname in csv_reader.fieldnames:
        if fname in include_columns or len(include_columns)==0:
            print(' '+(fname.ljust(arg_length[fname])[0:MAX_LENGTH-1])+' ', end='|')
    print('') 
    #Show all the lines
    input_file.seek(0)
    csv_reader = csv.DictReader(input_file, delimiter="\t")
    for row in csv_reader:
        for fname in csv_reader.fieldnames:
            if fname in include_columns or len(include_columns)==0:
                print(' '+(str(row[fname]).ljust(arg_length[fname])[0:MAX_LENGTH-1])+' ', end='|')
        print('')
    
