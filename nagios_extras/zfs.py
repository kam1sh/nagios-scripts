#!/usr/bin/env python3
import subprocess
import typing as ty
import logging

import nagiosplugin
from nagiosplugin import Metric, ScalarContext, Ok, Warn, Critical

from .nagios_support import ScalarPercentContext, Check, PerformanceContext

log = logging.getLogger(__name__)


class Pools(nagiosplugin.Resource):
    def __init__(self, names: ty.Iterable[str]):
        self.names = list(names)

    @property
    def name(self):
        return "ZPool"

    def probe(self):
        keys = "name,size,alloc,free,frag,dedup,health"
        cmd = "zpool list -H -p -o ".split() + [keys] + self.names
        output = subprocess.check_output(cmd).decode()
        keys = keys.split(",")
        for line in filter(None, output.split("\n")):
            info = dict(zip(keys, line.split("\t")))
            for k, v in info.items():
                if k in {"size", "alloc", "free", "frag"}:
                    info[k] = int(v)
                elif k == "dedup":
                    info[k] = float(v)

            yield from self.process(**info)

    def process(self, name, size, alloc, frag, health, **_):
        yield nagiosplugin.Metric("%s health" % name, value=health, context="health")
        yield nagiosplugin.Metric(name, value=alloc, min=0, max=size, context="pool")
        yield nagiosplugin.Metric(
            "%s fragmentation" % name, value=frag, min=0, max=100, context="frag"
        )


class HealthContext(nagiosplugin.Context):
    def evaluate(self, metric: Metric, resource) -> nagiosplugin.Result:
        if metric.value != "ONLINE":
            return self.result_cls(nagiosplugin.Critical, metric=metric)
        return self.result_cls(nagiosplugin.Ok, metric=metric)

def get_check(warn: str, crit: str, pools: tuple) -> Check:
    return Check(
        Pools(pools),
        ScalarPercentContext("pool", warn, crit, unit="B"),
        PerformanceContext("frag", unit="%"),
        HealthContext("health")
    )
