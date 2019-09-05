from setuptools import setup, find_packages


setup(
    name="nagios-extras",
    version="0.2.0",
    packages=["nagios_extras"],
    install_requires=[
        "click>=7.0", "nagiosplugin>=1.2.4", "humanize>=0.5.1", "pendulum>=2.0.5"
    ],
    tests_require=["pytest>=5.1.1", "pytest-mock>=1.10.4"],
    entry_points="""
    [console_scripts]
    nagplugins=nagios_extras.console:cli
""",
)
