cmake_minimum_required(VERSION 3.8)
project(car_tracker)

find_package(ament_cmake REQUIRED)

# Launch-only package -- no targets, just the launch tree and shared config.
#
# Build with --symlink-install so edits to launch/ and config/ take effect
# without a rebuild. camera.launch.py reads config/camera_wiring.yaml eagerly
# from the installed share directory, so without symlinks you would be editing
# a stale copy.
install(
        DIRECTORY launch config
        DESTINATION share/${PROJECT_NAME}/
)

# chain_check.py -- live health of the SLAM chain, link by link.
install(
        PROGRAMS scripts/chain_check.py
        DESTINATION lib/${PROJECT_NAME}
)

if (BUILD_TESTING)
    find_package(ament_lint_auto REQUIRED)
    ament_lint_auto_find_test_dependencies()
endif ()

ament_package()
