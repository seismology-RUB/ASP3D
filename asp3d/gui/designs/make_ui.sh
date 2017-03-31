#!/bin/bash
pyside-uic asp3d_layout.ui -o ../layouts/asp3d_layout.py
pyside-uic fmtomo_parameters_layout.ui -o ../layouts/fmtomo_parameters_layout.py
pyside-uic generate_seisarray_layout.ui -o ../layouts/generate_seisarray_layout.py
pyside-uic generate_survey_layout.ui -o ../layouts/generate_survey_layout.py
pyside-uic generate_survey_layout_minimal.ui -o ../layouts/generate_survey_layout_minimal.py
pyside-uic picking_parameters_layout.ui -o ../layouts/picking_parameters_layout.py
pyside-uic vtk_tools_layout.ui -o ../layouts/vtk_tools_layout.py
pyside-uic merge_shots_layout.ui -o ../layouts/merge_shots_layout.py
pyside-uic postprocessing_layout.ui -o ../layouts/postprocessing_layout.py
pyside-uic repicking_layout.ui -o ../layouts/repicking_layout.py
pyside-uic export2ascii_layout.ui -o ../layouts/export2ascii_layout.py
pyside-uic export_receiver_locations_layout.ui -o ../layouts/export_receiver_locations_layout.py
pyside-uic plot_shots_layout.ui -o ../layouts/plot_shots_layout.py
