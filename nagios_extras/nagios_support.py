import nagiosplugin
from nagiosplugin import Metric, Warn, Critical, Ok
from humanize import naturalsize


class PerformanceContext(nagiosplugin.Context):
    def __init__(
        self,
        name,
        unit="",
        fmt_metric="{name} is {valueunit}",
        result_cls=nagiosplugin.Result,
    ):
        super().__init__(name, fmt_metric=fmt_metric, result_cls=result_cls)
        self.performance_class = nagiosplugin.Performance
        self.unit = unit

    def performance(self, metric, resource):
        return self.performance_class(
            metric.name, metric.value, self.unit, None, None, metric.min, metric.max
        )


class ScalarPercentContext(PerformanceContext):
    """ Metric context that supports both scalar and percent thresholds. """

    def __init__(
        self, name, warn: str, crit: str, unit="", fmt_metric="{name} is {valueunit}"
    ):
        super().__init__(
            name, unit=unit, fmt_metric=fmt_metric, result_cls=nagiosplugin.Result
        )
        self.warn = warn
        self.crit = crit

    @staticmethod
    def parse_threshold(value: str, maximum: int):
        if isinstance(value, int):
            return value
        if value.endswith("%"):
            # 5% -> 0.05
            percents = int(value[:-1]) / 100
            return int(maximum - maximum * percents)
        else:
            return maximum - int(value)

    def evaluate(self, metric: Metric, resource) -> nagiosplugin.Result:
        """ Gets pool thresholds and compares them with args. """
        metric.warn_thresh = self.parse_threshold(self.warn, metric.max)
        metric.crit_thresh = self.parse_threshold(self.crit, metric.max)
        # if cmp(metric.value, self.warn, metric.max):
        if metric.warn_thresh <= metric.value:
            return self.result_cls(Warn, metric=metric)
        elif metric.crit_thresh <= metric.value:
            return self.result_cls(Critical, metric=metric)
        return self.result_cls(Ok, metric=metric)

    def performance(self, metric, resource):
        return self.performance_class(
            metric.name,
            metric.value,
            self.unit,
            metric.warn_thresh,
            metric.crit_thresh,
            metric.min,
            metric.max,
        )


class Runner(nagiosplugin.Runtime):
    def run(self, check):
        check()
        self.output.add(check)
        print(self.output)
        quit(check.exitcode)


class Check(nagiosplugin.Check):
    def main(self, verbose=None, timeout=None):
        runtime = Runner()
        runtime.run(self)
