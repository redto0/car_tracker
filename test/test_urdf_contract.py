"""The URDF contract: what the rest of the stack assumes about the robot model.

These are cheap, hardware-free, and catch the class of defect that otherwise
only shows up as a silent failure at runtime — a frame renamed in the URDF while
robot_wiring.yaml still names the old one, or the simulation description
accidentally changing the kinematics it is supposed to only decorate.

    colcon test --packages-select car_tracker
    colcon test-result --verbose
"""

import os
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml
from ament_index_python.packages import get_package_share_directory

_PKG = get_package_share_directory('car_tracker')
_HW_XACRO = os.path.join(
    get_package_share_directory('mentorpi_description'), 'urdf', 'mentorpi.xacro')
_SIM_XACRO = os.path.join(_PKG, 'urdf', 'mentorpi_sim.xacro')
_WIRING = os.path.join(_PKG, 'config', 'robot_wiring.yaml')


def _expand(xacro_path):
    """Run xacro. MACHINE_TYPE is what the vendor xacro dispatches on."""
    env = dict(os.environ, MACHINE_TYPE='MentorPi_Mecanum')
    out = subprocess.run(['xacro', xacro_path], capture_output=True, env=env)
    assert out.returncode == 0, (
        f'xacro failed on {xacro_path}:\n{out.stderr.decode()}')
    return ET.fromstring(out.stdout)


def _links(root):
    return {e.get('name') for e in root.findall('link')}


def _joints(root):
    return {(e.get('name'), e.get('type'),
             e.find('parent').get('link'), e.find('child').get('link'))
            for e in root.findall('joint')}


@pytest.fixture(scope='module')
def hardware():
    return _expand(_HW_XACRO)


@pytest.fixture(scope='module')
def simulation():
    return _expand(_SIM_XACRO)


def test_both_descriptions_expand(hardware, simulation):
    """Catches XML errors, undefined xacro properties, and bad includes.

    The '--' sequence is illegal inside an XML comment and is easy to type; it
    broke mentorpi.gazebo.xacro on first write.
    """
    assert _links(hardware), 'hardware URDF has no links'
    assert _links(simulation), 'simulation URDF has no links'


def test_simulation_does_not_change_the_kinematics(hardware, simulation):
    """The sim description decorates; it must not alter the robot.

    mentorpi_sim.xacro adds <gazebo> blocks only. If it ever changes a link,
    a joint, or an origin, the simulator stops testing the robot you ship.
    """
    assert _links(simulation) == _links(hardware), (
        'link sets differ between hardware and simulation descriptions:\n'
        f'  sim only: {sorted(_links(simulation) - _links(hardware))}\n'
        f'  hw only : {sorted(_links(hardware) - _links(simulation))}')
    assert _joints(simulation) == _joints(hardware), (
        'joint structure differs between hardware and simulation descriptions')


def test_frames_named_in_wiring_exist_in_the_urdf(hardware):
    """robot_wiring.yaml names frames; the URDF has to provide them.

    Nothing enforces this at runtime — a renamed link produces a TF lookup
    failure somewhere far from the cause, or silence.
    """
    with open(_WIRING) as f:
        frames = yaml.safe_load(f)['frames']
    links = _links(hardware)
    # odom and map are published by the filters, not links in the model
    expected = {v for k, v in frames.items() if k not in ('odom', 'map')}
    missing = expected - links
    assert not missing, (
        f'robot_wiring.yaml names frames that no URDF link provides: {sorted(missing)}\n'
        f'links present: {sorted(links)}')


def test_every_referenced_mesh_exists(simulation):
    """Unresolvable meshes spawn a robot with no geometry.

    Gazebo reports this as a warning, keeps going, and then queries the online
    model database — which is how it presented on 2026-09-17: a robot with no
    collision or visual geometry and no obvious error.
    """
    share_root = os.path.dirname(get_package_share_directory('mentorpi_description'))
    missing = []
    for mesh in simulation.iter('mesh'):
        uri = mesh.get('filename', '')
        if uri.startswith('model://'):
            path = os.path.join(share_root, uri[len('model://'):])
        elif uri.startswith('package://'):
            pkg, _, rel = uri[len('package://'):].partition('/')
            path = os.path.join(get_package_share_directory(pkg), rel)
        else:
            continue
        if not os.path.isfile(path):
            missing.append((uri, path))
    assert not missing, 'referenced meshes do not exist:\n' + '\n'.join(
        f'  {u}\n    -> {p}' for u, p in missing)


def test_simulation_does_not_broadcast_odom_tf(simulation):
    """planar_move must not publish odom or its TF.

    ekf_odom owns odom -> base_footprint. Two broadcasters on one edge make TF
    alternate between them. The shipped gazebo_plugins demo has both true, and
    this is the third occurrence of this failure in this project — after
    Hiwonder's enable_odom EKF and rf2o's publish_tf default.
    """
    for plugin in simulation.iter('plugin'):
        if 'planar_move' not in (plugin.get('filename') or ''):
            continue
        for tag in ('publish_odom', 'publish_odom_tf'):
            node = plugin.find(tag)
            assert node is not None, f'planar_move does not set {tag}'
            assert node.text.strip().lower() == 'false', (
                f'planar_move has {tag}={node.text!r}; ekf_odom owns that transform')
        return
    pytest.fail('no planar_move plugin found in the simulation description')
