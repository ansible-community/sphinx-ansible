#!/usr/bin/env python3

import pathlib
import yaml
import docutils.parsers.rst
import docutils.core
from sphinx.errors import ExtensionError

import ansible_runner


def write_play(play_content):
    tmp_dir = pathlib.Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    temp_file = tmp_dir / "temp_file.yaml"

    temp_file.write_text(play_content)
    return temp_file


def run_playbook(play_file):
    r = ansible_runner.run(
        private_data_dir=str(play_file.parent), playbook=play_file.name
    )
    return r


def get_outputs(play_file):
    r = run_playbook(play_file)
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


class CodeTestBlockDirective(docutils.parsers.rst.Directive):

    """Code block directive."""

    has_content = True
    optional_arguments = 1

    def run(self):
        """Run directive."""
        try:
            language = self.arguments[0]
        except IndexError:
            language = ""
        code = "\n".join(self.content)
        literal = docutils.nodes.literal_block(code, code)
        literal["classes"].append("code-test-block")
        literal["language"] = language
        return [literal]


class IgnoredDirective(docutils.parsers.rst.Directive):

    """Stub for unknown directives."""

    has_content = True

    def run(self):
        """Do nothing."""
        return []


def include_in_ansible_test_playbook(node):
    if node.tagname == "literal_block":
        if "code" in node.attributes["classes"]:
            return True
        elif "code-test-block" in node.attributes["classes"]:
            return True
    return False


def evaluate_playbook(play_content):
    play_file = write_play(play_content)
    outputs = get_outputs(play_file)
    return outputs


def evaluate_tasks(tasks):
    playbook_content = "- hosts: localhost\n  tasks:\n"
    for block in tasks:
        task_str = yaml.dump([block["task"]])
        new_lines = ["    " + l for l in task_str.split("\n")]
        playbook_content += "\n".join(new_lines) + "\n"
    return evaluate_playbook(playbook_content)
