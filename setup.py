import ez_setup

ez_setup.use_setuptools()

from setuptools import setup, find_packages

exec(open("lala/version.py").read())  # loads __version__

setup(
    name="python-lala",
    version=__version__,
    author="Zulko",
    description="Library of web access log analysis",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    license="MIT",
    keywords="access log analysis website webservice stats",
    packages=find_packages(exclude="docs"),
    install_requires=[
        "appdirs",
        "numpy",
        "matplotlib",
        "Pillow",
        "pygeoip",
        "pandas",
        "scipy",
        "proglog",
        "pdf_reports",
    ],
)
