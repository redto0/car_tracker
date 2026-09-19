"""Every package the launch tree uses must be declared in package.xml.

The project rule is that anything installed by hand -- apt, pip, anything --
gets declared as a rosdep instead. Nothing enforced it, so the drift was
invisible: a launch file referencing an undeclared package works perfectly on
the machine where someone already installed it, and fails on a fresh clone with
an error that names a missing package rather than a missing declaration.

    colcon test --packages-select car_tracker
"""

import os
import re
import xml.etree.ElementTree as ET

import pytest

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Package references a static scan can find.
_PATTERNS = (
    r"FindPackageShare\(\s*['\"]([a-z0-9_]+)['\"]",
    r"get_package_share_directory\(\s*['\"]([a-z0-9_]+)['\"]",
    r"package\s*=\s*['\"]([a-z0-9_]+)['\"]",
    r"^\s*package:\s*([a-z0-9_]+)\s*$",
)

# Invoked as commands, so nothing imports them and no scan would find them.
# Listed here so the test still requires them to be declared.
_COMMAND_DEPS = {'xacro', 'gazebo', 'teleop_twist_keyboard'}

_DEPEND_TAGS = ('exec_depend', 'depend', 'build_depend',
                'buildtool_depend', 'test_depend')


def _referenced():
    refs = {}
    for root, _dirs, files in os.walk(_HERE):
        if os.sep + 'test' in root:
            continue
        for name in files:
            if not (name.endswith('.launch.py') or name.endswith('.yaml')):
                continue
            path = os.path.join(root, name)
            with open(path) as f:
                text = f.read()
            for pat in _PATTERNS:
                for m in re.finditer(pat, text, re.M):
                    refs.setdefault(m.group(1), set()).add(
                        os.path.relpath(path, _HERE))
    return refs


def _declared():
    root = ET.parse(os.path.join(_HERE, 'package.xml')).getroot()
    return {e.text.strip() for e in root if e.tag in _DEPEND_TAGS}


def test_every_referenced_package_is_declared():
    refs = _referenced()
    declared = _declared()
    missing = sorted(set(refs) - declared - {'car_tracker'})
    assert not missing, (
        'packages used by the launch tree but not declared in package.xml:\n'
        + '\n'.join(f'  {p}  (referenced in {sorted(refs[p])[0]})' for p in missing))


def test_command_invoked_dependencies_are_declared():
    """These are run as processes, so no static scan would ever catch them."""
    missing = sorted(_COMMAND_DEPS - _declared())
    assert not missing, (
        'invoked as commands but not declared in package.xml: ' + ', '.join(missing))


@pytest.mark.parametrize('tag', _DEPEND_TAGS)
def test_no_duplicate_declarations(tag):
    root = ET.parse(os.path.join(_HERE, 'package.xml')).getroot()
    names = [e.text.strip() for e in root if e.tag == tag]
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert not dupes, f'declared more than once as <{tag}>: {dupes}'
