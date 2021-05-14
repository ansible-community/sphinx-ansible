import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="sphinx-ansible",
    description="Imagine a world where your documentation is also your Ansible playbook",
    version="0.0.2",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Gonéri Le Bouder",
    author_email="goneri@lebouder.net",
    install_requires=["ansible-runner"],
    url="https://github.com/ansible-community/sphinx-ansible",
    packages=["sphinxcontrib.sphinx_ansible"],
)
