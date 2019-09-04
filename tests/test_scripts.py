import subprocess

from click.testing import CliRunner
from nagios_extras import zfs, console
from nagiosplugin import Runtime


def patch_output(mocker, value):
    mocker.patch.object(subprocess, "check_output", return_value=value)


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
        "ZPOOL OK | 'pool1 fragmentation'=0%;;;0;100 "
        "pool1=2048B;7782;8110;0;8192\n\n"
    )
    assert result.exit_code == 0
