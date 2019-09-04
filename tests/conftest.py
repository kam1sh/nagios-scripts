import logging


def pytest_configure():
    log = logging.getLogger("nagios_extras").setLevel(logging.DEBUG)
