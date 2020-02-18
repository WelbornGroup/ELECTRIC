# Compile MDI
add_subdirectory(mdi)

# Add an __init__.py to the MDI directory, so that it can be used as a package
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/mdi/__init__.py "")

# Compile the driver
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/MDI_EF_Analysis.py ${CMAKE_CURRENT_BINARY_DIR}/MDI_EF_Analysis.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/util.py ${CMAKE_CURRENT_BINARY_DIR}/util.py COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/test_driver_functions.py ${CMAKE_CURRENT_BINARY_DIR}/test_driver_functions.py COPYONLY)
