# utils package
#
# MATPLOTLIBRC IS DROPPED HERE, BEFORE ANYTHING IMPORTS MATPLOTLIB.
#
# D-317 made the pipeline independent of a host matplotlib config, but the fix was one line
# in run_analysis.py. A script run DIRECTLY -- `python3 src/03_state_space_model.py`, or
# anything reached through --step -- never passes through the orchestrator, inherits the
# host's rc file, and writes figures with different text hinting. Measured 2026-11-08 in a
# cloud container carrying MATPLOTLIBRC=/etc/matplotlib: running Script 03 standalone
# modified six committed PNGs with no code change and no input change. Nothing caught it.
# The files are valid PNGs, so artefact_lint's Producer check passes, and they are
# internally consistent, so no gate has anything to compare against.
#
# This file is the earliest common point: every script reaches the pipeline through
# `from utils...`, and the package body runs before any submodule, so the variable is gone
# before matplotlib reads it. Popping it in render_utils would be too late when something
# else imports matplotlib first.
#
# The environment this project pins is tools/environment.json (D-227). A matplotlib config
# from outside the repository is not part of it, whichever route the script was started by.
import os as _os

_os.environ.pop("MATPLOTLIBRC", None)
del _os
