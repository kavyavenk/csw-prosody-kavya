#!/usr/bin/env python3
"""
Fix DisVoice scipy and Python 3 compatibility issues before importing.
"""

import sys
import scipy
import scipy.integrate
import scipy.fft
import urllib
import urllib.parse

# Patch 1: cumtrapz -> cumulative_trapezoid (scipy 1.9+)
if not hasattr(scipy.integrate, 'cumtrapz'):
    try:
        from scipy.integrate import cumulative_trapezoid
        scipy.integrate.cumtrapz = cumulative_trapezoid
    except ImportError:
        pass

# Patch 2: scipy.ifft -> scipy.fft.ifft (scipy 1.4+)
if not hasattr(scipy, 'ifft'):
    try:
        scipy.ifft = scipy.fft.ifft
    except AttributeError:
        try:
            from scipy.fft import ifft
            scipy.ifft = ifft
        except ImportError:
            pass

# Patch 3: urllib.quote -> urllib.parse.quote (Python 3)
if not hasattr(urllib, 'quote'):
    urllib.quote = urllib.parse.quote

# Patch 4: Also patch in the peakdetect module if needed
try:
    import disvoice.glottal.peakdetect as peakdetect_module
    if not hasattr(peakdetect_module, 'ifft'):
        peakdetect_module.ifft = scipy.fft.ifft
except:
    pass

# Patch 5: Patch parselmouth urllib issue BEFORE importing
# This needs to happen before parselmouth is imported
if not hasattr(urllib, 'quote'):
    # Monkey patch urllib before parselmouth imports it
    urllib.quote = urllib.parse.quote

print("DisVoice compatibility patches applied")

