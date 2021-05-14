#!/usr/bin/env python3

from docutils import nodes
from docutils.parsers.rst import Directive, directives


from sphinx.util.docutils import SphinxDirective
from sphinx.errors import ExtensionError

import json
import sphinxcontrib.sphinx_ansible.runner as runner
import yaml


class ansible_tasks_node(nodes.paragraph):
    pass


class ansible_playbook_node(nodes.paragraph):
    pass


class AnsibleTasksDirective(SphinxDirective):
    has_content = True
    has_content = True
    optional_arguments = 1
    option_spec = {
        "hide": directives.flag,  # Shall the block be hidden?
    }

    def run(self):
        task_ids = []

        if not hasattr(self.env, "ansible_tasks"):
            self.env.ansible_tasks = []

        try:
            yaml_data = yaml.load("\n".join(self.content), Loader=yaml.FullLoader)
        except yaml.error.MarkedYAMLError as e:
            raise ExtensionError(
                "Cannot parse the YAML of an Ansible block at: %s:%d\n  %s"
                % (self.env.docname, self.lineno, e)
            )
        code = "\n".join(self.content)

        if not yaml_data:
            raise ExtensionError(
                "The Ansible block at: %s:%d doesn't have any content."
                % (self.env.docname, self.lineno)
            )

        for task in yaml_data:
            task_id = "ansible_task-%s-%d-%d" % (
                self.env.docname,
                self.lineno,
                self.env.new_serialno("ansible_task"),
            )
            task["name"] = task_id
            task_ids.append(task_id)
            self.env.ansible_tasks.append(
                {"docname": self.env.docname, "lineno": self.lineno, "task": task}
            )

        my_ansible_tasks_node = ansible_tasks_node()
        if self.options.get("hide", False) is None:  # None: hide==True 😐...
            return []
        para_1 = nodes.paragraph()
        literal = nodes.literal_block(code, code)
        literal["language"] = "yaml"
        para_1 += literal
        para_2 = nodes.paragraph(ids=task_ids)
        para_2 += nodes.Text("response", "response")
        my_ansible_tasks_node += para_1
        my_ansible_tasks_node += para_2
        return [my_ansible_tasks_node]


class AnsiblePlaybookDirective(SphinxDirective):
    has_content = True

    def run(self):
        playbook_id = "ansible_playbook-%d" % self.env.new_serialno("ansible_task")
        if not hasattr(self.env, "ansible_playbooks"):
            self.env.ansible_playbooks = {}

        code = "\n".join(self.content)
        self.env.ansible_playbooks[playbook_id] = {
            "docname": self.env.docname,
            "lineno": self.lineno,
            "code": code,
        }

        my_ansible_playbook_node = ansible_playbook_node()
        para_1 = nodes.paragraph()
        literal = nodes.literal_block(code, code)
        literal["language"] = "yaml"
        para_1 += literal
        para_2 = nodes.paragraph(ids=[playbook_id])
        para_2 += nodes.Text("response", "response")
        my_ansible_playbook_node += para_1
        my_ansible_playbook_node += para_2
        return [my_ansible_playbook_node]


def purge_ansible_tasks(app, env, docname):
    # NOTE: this won't work if tasks share facts between two .rst doc
    if not hasattr(env, "ansible_tasks"):
        return

    env.ansible_tasks = [
        ansible_task
        for ansible_task in env.ansible_tasks
        if ansible_task["docname"] != docname
    ]
    if not hasattr(env, "ansible_playbooks"):
        return

    env.ansible_playbooks = {
        playbook_id: ansible_playbook
        for playbook_id, ansible_playbook in env.ansible_playbooks.items()
        if ansible_playbook["docname"] != docname
    }


def merge_ansible_tasks(app, env, docnames, other):
    if not hasattr(env, "ansible_tasks"):
        env.ansible_tasks = []
    if hasattr(other, "ansible_tasks"):
        env.ansible_tasks.extend(other.ansible_tasks)
    if not hasattr(env, "ansible_playbooks"):
        env.ansible_playbooks = []
    if hasattr(other, "ansible_playbooks"):
        env.ansible_playbooks.extend(other.ansible_playbooks)


def process_ansible_tasks_nodes(app, doctree, fromdocname):

    env = app.builder.env
    if not hasattr(env, "ansible_tasks"):
        env.ansible_tasks = []

    if not hasattr(env, "ansible_results"):
        env.ansible_results = runner.evaluate_tasks(
            env.ansible_tasks,
            roles_path=app.config.ansible_roles_path,
            tmp_dir=app.config.ansible_tmp_dir,
        )

    for node in doctree.traverse(ansible_tasks_node):
        if not node:  # hidden
            return
        for task_id in node[1].get("ids"):
            result_data = env.ansible_results.get(task_id)
            if not result_data:
                return
            for i in [
                "_ansible_no_log",
                "invocation",
                "_ansible_verbose_always",
                "_debug_info",
            ]:
                if i in result_data:
                    del result_data[i]
            result_string = json.dumps(result_data, sort_keys=True, indent=4)
            literal = nodes.literal_block(result_string, result_string)
            literal["language"] = "json"
            node[1] += literal


def process_ansible_playbook_nodes(app, doctree, fromdocname):

    env = app.builder.env
    if not hasattr(env, "ansible_playbooks"):
        env.ansible_playbooks = {}

    if not hasattr(env, "ansible_results"):
        env.ansible_results = {}

    for playbook_id, content in env.ansible_playbooks.items():
        play_file = runner.write_play(
            content["code"], tmp_dir=app.config.ansible_tmp_dir,
        )
        env.ansible_results[playbook_id] = runner.run_playbook(
            play_file, roles_path=app.config.ansible_roles_path,
        )

    for node in doctree.traverse(ansible_playbook_node):
        playbook_id = node[1].get("ids")[0]
        result_string = env.ansible_results.get(playbook_id).stdout.read()
        literal = nodes.literal_block(result_string, result_string)
        node[1] += literal


def setup(app):
    app.add_config_value("ansible_roles_path", [], "html")
    app.add_config_value("ansible_tmp_dir", "tmp_dir_sphinx_ansible", "html")

    app.add_directive("ansible-task", AnsibleTasksDirective)
    app.add_directive("ansible-tasks", AnsibleTasksDirective)
    app.add_directive("ansible-playbook", AnsiblePlaybookDirective)
    app.connect("doctree-resolved", process_ansible_tasks_nodes)
    app.connect("doctree-resolved", process_ansible_playbook_nodes)
    app.connect("env-purge-doc", purge_ansible_tasks)
    app.connect("env-merge-info", merge_ansible_tasks)

    return {
        "version": "0.1",
        "parallel_read_safe": False,
        "parallel_write_safe": False,
    }
