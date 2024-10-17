import pytest

from package_manager import PackageManagerApk
from version import Version, VersionConditional


@pytest.fixture
def pkg_man() -> PackageManagerApk:
    return PackageManagerApk()


def test_none(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['apk', 'update'])
    assert packages == []


def test_no_conditional(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.NONE
    assert packages[0].version_str is None


def test_wrong_argument_order(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['add', 'apk', 'git'])
    assert packages == []


def test_less_than(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git<2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.LESS_THAN
    assert packages[0].version_str == '2.43.0'


def test_equality(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git=2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.EQUALITY
    assert packages[0].version_str == '2.43.0'
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git==2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.EQUALITY
    assert packages[0].version_str == '2.43.0'


def test_larger_than(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git>2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.GREATER_THAN
    assert packages[0].version_str == '2.43.0'


def test_fuzzy(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git~2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.FUZZY
    assert packages[0].version_str == '2.43.0'
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git~=2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.FUZZY
    assert packages[0].version_str == '2.43.0'
    packages = pkg_man._parse_install_package_subcommand(['apk', 'add', 'git=~2.43.0'])
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.FUZZY
    assert packages[0].version_str == '2.43.0'


def test_multiple(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(
        ['apk', 'add', 'git=2.43.0', 'nginx<1.26.2', 'ripgrep>14.1.1', 'astyle=~3.6.3']
    )
    assert len(packages) == 4
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.EQUALITY
    assert packages[0].version_str == '2.43.0'
    assert packages[1].name == 'nginx'
    assert packages[1].conditional == VersionConditional.LESS_THAN
    assert packages[1].version_str == '1.26.2'
    assert packages[2].name == 'ripgrep'
    assert packages[2].conditional == VersionConditional.GREATER_THAN
    assert packages[2].version_str == '14.1.1'
    assert packages[3].name == 'astyle'
    assert packages[3].conditional == VersionConditional.FUZZY
    assert packages[3].version_str == '3.6.3'


def test_flags(pkg_man: PackageManagerApk) -> None:
    packages = pkg_man._parse_install_package_subcommand(
        ['PATH=/usr/local/bin', 'sudo', 'apk', '-q', '-i', 'add', '--initdb', '-t', 'NAME', 'git=2.43.0']
    )
    assert len(packages) == 1
    assert packages[0].name == 'git'
    assert packages[0].conditional == VersionConditional.EQUALITY
    assert packages[0].version_str == '2.43.0'


def test_create_update_and_list_package_versions_command_empty(pkg_man: PackageManagerApk) -> None:
    with pytest.raises(RuntimeError):
        pkg_man.create_update_and_list_package_versions_command([])


def test_create_update_and_list_package_versions_command_one(pkg_man: PackageManagerApk) -> None:
    command = pkg_man.create_update_and_list_package_versions_command(['git'])
    assert command == 'apk update -q && apk list git'


def test_create_update_and_list_package_versions_command_multiple(pkg_man: PackageManagerApk) -> None:
    command = pkg_man.create_update_and_list_package_versions_command(['git', 'nginx', 'ripgrep'])
    assert command == 'apk update -q && apk list git nginx ripgrep'


def test_parse_version_string(pkg_man: PackageManagerApk) -> None:
    version = pkg_man.parse_version_string('git', '2.45.2-r0')
    assert version == Version('2.45.2-r0', 'git', 2, 45, 2, 0)

    version = pkg_man.parse_version_string('git', '2.45.2')
    assert version == Version('2.45.2', 'git', 2, 45, 2)

    version = pkg_man.parse_version_string('git', '2.45')
    assert version == Version('2.45', 'git', 2, 45)

    version = pkg_man.parse_version_string('git', '2')
    assert version == Version('2', 'git', 2)

    version = pkg_man.parse_version_string('git', 'prerelease')
    assert version is None


def test_parse_version(pkg_man: PackageManagerApk) -> None:
    package_version_str = 'git-2.45.2-r0 x86_64 {git} (GPL-2.0-only)'
    version = pkg_man.parse_version(package_version_str)
    assert version == Version('2.45.2-r0', 'git', 2, 45, 2, 0)
