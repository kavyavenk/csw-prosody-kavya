# -*- coding: utf-8 -*-
"""
prep_audios.py

MFA expects the following corpus structure:
    
+-- textgrid_corpus_directory
|   --- recording1.wav
|   --- recording1.TextGrid
|   --- recording2.wav
|   --- recording2.TextGrid
|   --- ...

Audios are currently filed like this:
+-- audio_segments
|   --- 01NC01FBX_0101
|       --- 01NC01FBX_0101_26.384_27.712.wav
|       --- ...
|   --- ...
    
This script will reorganize audio files into the correct corpus structure.

Usage:
    python prep_audios.py <path_to_audio_segments> <path_to_conversation_textgrids> <path_to_interview_textgrids>

Created on Sat May  4 14:33:54 2024

@author: emlin
"""
import os
import sys

def main():
    for subset in sys.argv[2:4]:
        for tg in os.listdir(subset):
            if tg.endswith(".TextGrid"):
                prefix = "_".join(tg.split("_")[:-2])
                
                dest = os.path.join(subset,
                                    tg.replace(".TextGrid",
                                               ".wav"))
                
                try:
                    os.rename(os.path.join(sys.argv[1],
                                           prefix,
                                           tg.replace(".TextGrid",
                                                      ".wav")),
                              dest)
                except FileNotFoundError as e:
                    print(e,
                          "Could not file WAV for {}".format(tg))
if __name__ == "__main__":
    main()