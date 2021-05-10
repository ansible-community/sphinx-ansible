from setuptools import setup

setup(
    name="sphinx-ansible",
    description="Imagine a world where your documentation is also your Ansible playbook",
    version="0.0.1",
    author="Gonéri Le Bouder",
    author_email="goneri@lebouder.net",
    install_requires=["ansible-runner"],
    url="https://github.com/goneri/sphinx-ansible",
    packages=["sphinxcontrib.sphinx_ansible"],
)
