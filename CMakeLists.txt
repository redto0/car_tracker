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
        DIRECTORY launch config urdf worlds
        DESTINATION share/${PROJECT_NAME}/
)

# chain_check.py -- live health of the SLAM chain, link by link.
install(
        PROGRAMS scripts/chain_check.py scripts/dynamic_probe.py
        DESTINATION lib/${PROJECT_NAME}
)

if (BUILD_TESTING)
    find_package(ament_lint_auto REQUIRED)
    ament_lint_auto_find_test_dependencies()

    # The URDF contract: the frames the wiring names must exist, the meshes must
    # resolve, and the simulation description must decorate the robot without
    # changing its kinematics. Hardware-free, so it runs anywhere.
    #
    # Registered with ament_add_test rather than ament_add_pytest_test on
    # purpose. The latter probes for pytest at configure time, and that probe
    # fails on any machine where a user-site package breaks pytest's plugin
    # autoload -- as anyio 4.13.0 in ~/.local does here against pytest 6.2.5,
    # which has no _pytest.scope. ament_add_pytest_test then emits a warning
    # and silently registers NOTHING, so `colcon test` passes while running no
    # tests at all. That failure mode is worse than the environment problem.
    #
    # PYTHONNOUSERSITE=1 sidesteps the broken plugin; MACHINE_TYPE is what the
    # vendor xacro dispatches on.
    find_package(ament_cmake_test REQUIRED)
    ament_add_test(test_urdf_contract
            COMMAND ${CMAKE_COMMAND} -E env
                    PYTHONNOUSERSITE=1
                    MACHINE_TYPE=MentorPi_Mecanum
                    python3 -m pytest
                    ${CMAKE_CURRENT_SOURCE_DIR}/test/test_urdf_contract.py
                    -v
                    --junit-xml=${AMENT_TEST_RESULTS_DIR}/${PROJECT_NAME}/test_urdf_contract.xunit.xml
            TIMEOUT 120
            GENERATE_RESULT_FOR_RETURN_CODE_ZERO)
endif ()

ament_package()
