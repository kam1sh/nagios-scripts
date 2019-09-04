import click
import nagiosplugin

from . import __version__, zfs


@click.group()
@click.version_option(__version__, prog_name="nagios-extras")
def cli():
    pass


@cli.command()
@click.argument("pool", nargs=-1, required=True)
@click.option("-w", "warn", help="Warning threshold (integer or %)")
@click.option("-c", "crit", help="Warning threshold (integer or %)")
def zpool(pool, warn, crit):
    check = zfs.get_check(warn=warn, crit=crit, pools=pool)
    check.main()
