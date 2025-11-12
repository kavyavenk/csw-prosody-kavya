PY := python
SCRIPTS := scripts

.PHONY: all normalize manifest slice features contrasts plots         normalize_seame manifest_seame slice_seame features_seame contrasts_seame plots_seame

# MaSaC pipeline
all: normalize manifest slice features contrasts

normalize:
	$(PY) $(SCRIPTS)/00_normalize_audio.py --corpus masac
manifest:
	$(PY) $(SCRIPTS)/01_build_manifest.py --corpus masac
slice:
	$(PY) $(SCRIPTS)/02_slice_by_timestamps.py --corpus masac
features:
	$(PY) $(SCRIPTS)/03_extract_disvoice_utterance.py --corpus masac
contrasts:
	$(PY) $(SCRIPTS)/04_first_contrasts.py --corpus masac
plots:
	$(PY) $(SCRIPTS)/05_plot_quick.py --corpus masac

# SEAME pipeline
normalize_seame:
	$(PY) $(SCRIPTS)/00_normalize_audio.py --corpus seame
manifest_seame:
	$(PY) $(SCRIPTS)/01_build_manifest.py --corpus seame
slice_seame:
	$(PY) $(SCRIPTS)/02_slice_by_timestamps.py --corpus seame
features_seame:
	$(PY) $(SCRIPTS)/03_extract_disvoice_utterance.py --corpus seame
contrasts_seame:
	$(PY) $(SCRIPTS)/04_first_contrasts.py --corpus seame
plots_seame:
	$(PY) $(SCRIPTS)/05_plot_quick.py --corpus seame
