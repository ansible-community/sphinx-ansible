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


def wrap_in_one_cell_tab(node):
    table = nodes.table()
    group = nodes.tgroup("", cols=1)
    group.append(nodes.colspec("", colwidth=10))
    table.append(group)
    body = nodes.tbody("")
    row = nodes.row("")
    body.append(row)
    row.append(nodes.entry("", node))
    group.append(body)
    return table


def build_directive_output(code, anchor, use_one_cell_tab=False):
    result_node = ansible_tasks_node()
    if use_one_cell_tab:
        para_1 = nodes.paragraph()
        literal = nodes.literal_block(code, code)
        literal["language"] = "yaml"
        para_1 += wrap_in_one_cell_tab(literal)
        para_2 = nodes.paragraph()
        para_2 += nodes.Text("Response:", "Response:")
        para_3 = nodes.paragraph()
        para_3 += wrap_in_one_cell_tab(nodes.paragraph(ids=[anchor]))
        result_node += para_1
        result_node += para_2
        result_node += para_3

    else:
        para_1 = nodes.paragraph()
        literal = nodes.literal_block(code, code)
        literal["language"] = "yaml"
        para_1 += literal
        para_2 = nodes.paragraph(ids=[anchor])
        para_2 += nodes.Text("Response:", "Response:")
        result_node += para_1
        result_node += para_2
    return [result_node]


class AnsibleTasksDirective(SphinxDirective):
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

        if "hide" in self.options:
            return []
        return build_directive_output(
            code, anchor=task_id, use_one_cell_tab=self.config.ansible_use_one_cell_tab
        )


class AnsiblePlaybookDirective(SphinxDirective):
    has_content = True
    optional_arguments = 1
    option_spec = {
        "hide": directives.flag,  # Shall the block be hidden?
    }

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

        if "hide" in self.options:
            return []
        return build_directive_output(
            code,
            anchor=playbook_id,
            use_one_cell_tab=self.config.ansible_use_one_cell_tab,
        )


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
        if app.config.ansible_use_one_cell_tab:
            target_p = node[2][0][0][1][0][0][0]
        else:
            target_p = node[1]
        for task_id in target_p.get("ids"):
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
            target_p += literal


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
        if app.config.ansible_use_one_cell_tab:
            target_p = node[2][0][0][1][0][0][0]
        else:
            target_p = node[1]

        playbook_id = target_p.get("ids")[0]
        result_string = env.ansible_results.get(playbook_id).stdout.read()
        literal = nodes.literal_block(result_string, result_string)
        target_p += literal


def setup(app):
    app.add_config_value("ansible_roles_path", [], "html")
    app.add_config_value("ansible_tmp_dir", "tmp_dir_sphinx_ansible", "html")
    app.add_config_value("ansible_use_one_cell_tab", False, "html")

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
