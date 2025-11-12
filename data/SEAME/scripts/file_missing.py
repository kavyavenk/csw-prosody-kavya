# -*- coding: utf-8 -*-
"""
file_missing.py

Created on Sat May  4 15:32:23 2024

python prep_audios.py <path_to_file_missing_audio_segments> <path_to_conversation_textgrids> <path_to_interview_textgrids>

@author: emlin
"""
import os
import sys

def main():
    i = 0
    for subset in sys.argv[2:4]:
        files = set(os.listdir(subset))
        
        for tg in os.listdir(subset):
            if tg.endswith(".TextGrid"):
                # missing audio
                if tg.replace(".TextGrid", ".wav") not in files:
                    os.rename(os.path.join(subset,
                                           tg),
                              os.path.join(sys.argv[1],
                                           tg))
                    i += 1
                    
                    if i%1000 == 0:
                        print("Filed {} files".format(i))
    
if __name__ == "__main__":
    main()