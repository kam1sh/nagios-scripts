import click
import nagiosplugin

from . import __version__, zfs, restic


@click.group()
@click.version_option(__version__, prog_name="nagios-extras")
def cli():
    pass


@cli.command()
@click.argument("pool", nargs=-1, required=True)
@click.option("-w", "warn", default="5%", help="Warning threshold (integer or %)")
@click.option("-c", "crit", default="1%", help="Warning threshold (integer or %)")
def zpool(pool, warn, crit):
    check = zfs.get_check(warn=warn, crit=crit, pools=pool)
    check.main()


@cli.command()
@click.option("-w", "warn", required=True, help="Warning threshold (hours)")
@click.option("-c", "crit", required=True, help="Critical threshold (hours)")
@click.option("--bin", "executable", help="Restic executable")
@click.option("--host", multiple=True, help="Host to filter")
@click.option("--path", multiple=True, help="Path to filter")
@click.option("--tag", multiple=True, help="Tag to filter")
def restic_snapshots(executable, warn, crit, host, path, tag):
    check = restic.get_check(warn, crit, host=host, path=path, tags=tag)
    check.main()
