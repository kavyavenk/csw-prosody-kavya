# -*- coding: utf-8 -*-
"""
get_textgrids.py

Parse textgrids from SEAME data.

Montreal Forced Aligner expects TextGrids with tiers named by speaker.

Usage:
    
    python get_textgrids.py <path_to_seame_corpus_csv> <language>

Created on Sat May  4 10:12:26 2024

@author: emlin
"""

import csv
import os
import sys
from praatio import textgrid
from praatio.utilities.constants import Interval

FIELDS = {"row_number": 0,
          "original_row_number": 1,
          "file": 2,
          "conversation": 3,
          "speaker": 4,
          "type": 8,
          "start_time": 9,
          "end_time": 10,
          "transcript_2015": 13,
          "language": 23}

def make_textgrid(row: list):
    tg = textgrid.Textgrid()
    
    utt = Interval(0, 
                   int(row[FIELDS["end_time"]])/1000, 
                   row[FIELDS["transcript_2015"]])
    
    utts = textgrid.IntervalTier(row[FIELDS["speaker"]],
                                 [utt],
                                 0, 
                                 int(row[FIELDS["end_time"]])/1000)
    
    tg.addTier(utts)
    
    return tg

def main():
    # https://docs.python.org/3/library/csv.html
    with open(sys.argv[1], newline="", encoding="utf-8") as csvfile:
        r = csv.reader(csvfile, quotechar="|")
        
        next(r) # skip header
        
        i = 0
        
        for row in r:
            # only parse rows of specified language
            if row[FIELDS["language"]] == sys.argv[2]:
                
                make_textgrid(row).save(os.path.join(row[FIELDS["type"]].lower(),
                                                     "{}_{}_{}.TextGrid".format(row[FIELDS["file"]],
                                                                                float(row[FIELDS["start_time"]])/1000,
                                                                                float(row[FIELDS["end_time"]])/1000)), 
                                        "long_textgrid", 
                                        includeBlankSpaces=True)
            
            i += 1
            if i%1000 == 0:
                print("Parsed {} rows".format(i))
if __name__ == "__main__":
    main()