# Compile MDI
add_subdirectory(mdi)

# Add an __init__.py to the MDI directory, so that it can be used as a package
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/mdi/__init__.py "")



# Locate MPI

find_package(MPI)
if(MPI_FOUND)
   include_directories(${MPI_INCLUDE_PATH})
else()
   configure_file(${CMAKE_CURRENT_SOURCE_DIR}/STUBS_MPI/mpi.h ${CMAKE_CURRENT_BINARY_DIR}/STUBS_MPI/mpi.h COPYONLY)
endif()



# Link to MDI

set( MDI_LOCATION ${CMAKE_CURRENT_BINARY_DIR}/mdi/MDI_Library/ )
link_directories( ${MDI_LOCATION} )
include_directories(${MDI_LOCATION})



# Compile the driver

add_executable(MDI_EF_Analysis
               MDI_EF_Analysis.cpp)
target_link_libraries(MDI_EF_Analysis mdi
                      ${MPI_LIBRARIES})

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/MDI_EF_Analysis.py ${CMAKE_CURRENT_BINARY_DIR}/MDI_EF_Analysis.py COPYONLY)



# Ensure that MPI is properly linked

if(NOT MPI_FOUND)
   target_include_directories(MDI_EF_Analysis PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/STUBS_MPI/)
endif()
if(MPI_COMPILE_FLAGS)
   set_target_properties(MDI_EF_Analysis PROPERTIES
      COMPILE_FLAGS "${MPI_COMPILE_FLAGS}")
endif()
if(MPI_LINK_FLAGS)
   set_target_properties(MDI_EF_Analysis PROPERTIES
      LINK_FLAGS "${MPI_LINK_FLAGS}")
endif()
