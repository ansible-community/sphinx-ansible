#!/usr/bin/env python3

import pathlib
import yaml
import docutils.parsers.rst
import docutils.core
from sphinx.errors import ExtensionError
from sphinx.util import logging

import ansible_runner


logger = logging.getLogger(__name__)


def write_play(play_content, tmp_dir):
    tmp_dir = pathlib.Path(tmp_dir)
    tmp_dir.mkdir(exist_ok=True)
    temp_file = tmp_dir / "temp_file.yaml"
    temp_file.write_text(play_content)
    return temp_file


def run_playbook(play_file, roles_path=None):
    logger.info("[ansible_runner] Running: {}".format(play_file))
    r = ansible_runner.run(
        private_data_dir=str(play_file.parent),
        playbook=play_file.name,
        roles_path=roles_path,
    )
    return r


def get_outputs(play_file, roles_path=None):
    r = run_playbook(play_file, roles_path=roles_path)
    if r.rc:
        raise ExtensionError("ansible execution has failed")
    outputs = {}
    for each_host_event in r.events:
        if each_host_event["event"] == "runner_on_ok":
            event_data = each_host_event["event_data"]
            task = each_host_event["event_data"].get("task")
            res = each_host_event["event_data"].get("res")
            if not (task and res):
                continue
            if task == "Gathering Facts":
                continue

            print(f"{task}> {res}")
            outputs[task] = res
    return outputs


def evaluate_playbook(play_content, roles_path=None, tmp_dir=None):
    play_file = write_play(play_content, tmp_dir=tmp_dir)
    outputs = get_outputs(play_file, roles_path=roles_path)
    return outputs


def evaluate_tasks(tasks, roles_path=None, tmp_dir=None):
    playbook_content = "- hosts: localhost\n  tasks:\n"
    for block in tasks:
        task_str = yaml.dump([block["task"]])
        new_lines = ["    " + l for l in task_str.split("\n")]
        playbook_content += "\n".join(new_lines) + "\n"
    return evaluate_playbook(playbook_content, roles_path=roles_path, tmp_dir=tmp_dir)
