"""Shared test fixtures for Monitor Layout Manager tests.

Headless-safe: no tkinter imports anywhere in the test suite.
"""

import os
import sys

import pytest

# Make the project root importable (core/, utils/, cli/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Realistic displayplacer v1.4.0 `list` output: MacBook built-in (main) +
# two externals, one with a negative origin (above/left of main).
# Persistent ids are anonymized.
DISPLAYPLACER_LIST_OUTPUT = """\
Persistent screen id: AAAAAAAA-1111-2222-3333-444444444444
Contextual screen id: 1
Serial screen id: s1000000001
Type: MacBook built in screen
Resolution: 1728x1117
Hertz: 120
Color Depth: 8
Scaling: on
Origin: (0,0) - main display
Rotation: 0 - rotate internal screen example (may crash computer, but will be rotated after rebooting): `displayplacer "id:AAAAAAAA-1111-2222-3333-444444444444 degree:90"`
Enabled: true
Resolutions for rotation 0:
  mode 0: res:960x600 hz:120 color_depth:8 scaling:on
  mode 1: res:960x600 hz:60 color_depth:8 scaling:on
  mode 2: res:1280x800 hz:120 color_depth:8 scaling:on
  mode 3: res:1280x800 hz:60 color_depth:8 scaling:on
  mode 4: res:1728x1117 hz:120 color_depth:8 scaling:on
  mode 5: res:1728x1117 hz:60 color_depth:8 scaling:on
Persistent screen id: BBBBBBBB-1111-2222-3333-444444444444
Contextual screen id: 2
Serial screen id: s1000000002
Type: 27 inch external screen
Resolution: 1920x1080
Hertz: 60
Color Depth: 8
Scaling: off
Origin: (1728,-996)
Rotation: 0
Enabled: true
Resolutions for rotation 0:
  mode 0: res:800x600 hz:75 color_depth:8
  mode 1: res:1920x1080 hz:60 color_depth:8 scaling:on
  mode 2: res:1920x1080 hz:50 color_depth:8 scaling:on
  mode 3: res:2560x1440 hz:60 color_depth:8 scaling:off
Persistent screen id: CCCCCCCC-1111-2222-3333-444444444444
Contextual screen id: 3
Serial screen id: s1000000003
Type: 32 inch external screen
Resolution: 1920x1080
Hertz: N/A
Color Depth: 8
Scaling: on
Origin: (-192,-1080)
Rotation: 0
Enabled: true
Resolutions for rotation 0:
  mode 0: res:1920x1080 hz:100 color_depth:8 scaling:on
  mode 1: res:1920x1080 hz:60 color_depth:8 scaling:on
  mode 2: res:3840x2160 hz:60 color_depth:8 scaling:off
"""

MACBOOK_ID = "AAAAAAAA-1111-2222-3333-444444444444"
EXTERNAL_27_ID = "BBBBBBBB-1111-2222-3333-444444444444"
EXTERNAL_32_ID = "CCCCCCCC-1111-2222-3333-444444444444"


@pytest.fixture
def displayplacer_output():
    return DISPLAYPLACER_LIST_OUTPUT
