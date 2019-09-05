import json
import subprocess

from click.testing import CliRunner
from nagios_extras import zfs, console, restic
import pendulum


def patch_output(mocker, value, sideeffect=False):
    mocker.patch.object(subprocess, "check_output")
    if sideeffect:
        subprocess.check_output.side_effect = value
    else:
        subprocess.check_output.return_value = value


def test_cmp():
    parse = zfs.ScalarPercentContext.parse_threshold
    assert parse("5%", maximum=2048) == 1945
    assert parse("5", maximum=2048) == 2043
    assert parse("100%", maximum=2048) == 0
    assert parse("0%", maximum=2048) == 2048


def test_zpool(mocker):
    # name,size,alloc,free,frag,dedup,health
    output = b"""
pool1\t8192\t4096\t4096\t0\t1.00\tONLINE
pool2\t16384\t4592\t11792\t0\t1.00\tONLINE
"""
    patch_output(mocker, output)
    check = zfs.get_check(warn="5%", crit="1%", pools=("pool1", "pool2"))
    check()
    print(check.summary_str)
    assert check.exitcode == 0


def test_zpool_degraded(mocker):
    output = b"""
    pool1\t8192\t4096\t4096\t0\t1.00\tDEGRADED
"""
    patch_output(mocker, output)
    check = zfs.get_check("1", "1", pools=("pool1",))
    check()
    assert check.exitcode == 2


def test_cli(mocker):
    output = b"pool1\t8192\t2048\t6144\t0\t1.00\tONLINE"
    patch_output(mocker, output)
    runner = CliRunner()
    result = runner.invoke(console.cli, ["zpool", "-w", "5%", "-c", "1%", "pool1"])
    print(result.output)
    assert result.output == (
        "ZPOOL OK | pool1=2048B;7782;8110;0;8192 "
        "pool1_fragmentation=0%;;;0;100\n\n"
    )
    assert result.exit_code == 0

def mock_restic(mocker, time, size=None, files=None):
    outputs = [
        json.dumps([{
            "time": str(time),
            "parent": "a11701fb65a31017594d715fa7a8f71b2fb466acd7c13b766cf268bfd012eee0",
            "tree": "0d9bad27a71247905de7436e3a9446b491b001f3eae08cad656d3a3f606ef4e8",
            "paths": [
                "/home",
                "/etc"
            ],
            "hostname": "server",
            "username": "backups",
            "uid": 1005,
            "gid": 1005,
            "tags": ["home-etc"],
            "id": "9e4dc59390b38da3753042d91988ba856a2a98deb2425afa11c9a1f5ed4846b3",
            "short_id": "9e4dc593"
        }]),
        json.dumps({"total_size": size or 112660249, "total_file_count": files or 7670})
    ]
    patch_output(mocker, outputs, sideeffect=True)

def test_restic_ok(mocker):
    mock_restic(mocker, time=pendulum.now().subtract(hours=2))
    check = restic.get_check(hours_warn=3, hours_crit=4)
    check()
    print(check.summary_str)
    assert check.exitcode == 0

def test_restic_warn(mocker):
    mock_restic(mocker, time=pendulum.now().subtract(hours=25))
    check = restic.get_check(hours_warn=24, hours_crit=48)
    check()
    print(check.summary_str)
    assert check.exitcode == 1

def test_restic_crit(mocker):
    mock_restic(mocker, time=pendulum.now().subtract(hours=72))
    check = restic.get_check(hours_warn=24, hours_crit=48)
    check()
    print(check.summary_str)
    assert check.exitcode == 2

def test_restic_cli(mocker):
    mock_restic(mocker, time=pendulum.now().subtract(hours=72))
    runner = CliRunner()
    result = runner.invoke(console.cli, ["restic-snapshots", "-w", "24", "-c", "48"])
    print(result.output)
    assert result.output == (
        "RESTICREPO CRITICAL - home-etc is 72 (outside range 0:48) | "
        "'home-etc'=72;24;48;0 total_files=7670c total_size=112660249B\n\n"
    )
    assert result.exit_code == 2
