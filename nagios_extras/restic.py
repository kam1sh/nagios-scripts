import json
import subprocess

import pendulum
import nagiosplugin
from nagiosplugin import Metric

from .nagios_support import ScalarPercentContext, Check, PerformanceContext


def tolist(val):
    if isinstance(val, str):
        return [val]
    elif hasattr(val, "__iter__"):
        return list(val)
    return []

class ResticRepo(nagiosplugin.Resource):
    """ Gets snapshot metrics from Restic repository defined in environment variable. """

    def __init__(self, executable=None, host=None, path=None, tags=None):
        self.executable = executable or "/usr/local/bin/restic"
        self.host = host
        self.paths = tolist(path)
        self.tags = tolist(tags)

    def probe(self):
        cmd = [self.executable, "--json", "snapshots", "--last"]
        if self.host:
            cmd += ["--host", self.host]
        for path in self.paths:
            cmd += ["--path", path]
        for tag in self.tags:
            cmd += ["--tag", tag]
        output = subprocess.check_output(cmd)
        for snapshot in json.loads(output):
            when = pendulum.parse(snapshot["time"])
            hours_old = (pendulum.now() - when).in_hours()
            label = snapshot["tags"][0] if snapshot["tags"] else snapshot["short_id"]
            yield Metric(label, hours_old, min=0, context="snapshot")
        output = subprocess.check_output([self.executable, "--json", "stats"])
        stats = json.loads(output)
        yield Metric("total_size", stats["total_size"], uom="B", context="size")
        yield Metric("total_files", stats["total_file_count"], uom="c", context="files")

def get_check(hours_warn, hours_crit, host=None, path=None, tags=None):
    return Check(
        ResticRepo(host=host, path=path, tags=tags),
        nagiosplugin.ScalarContext("snapshot", warning=hours_warn, critical=hours_crit),
        nagiosplugin.ScalarContext("size"),
        nagiosplugin.ScalarContext("files")
    )
