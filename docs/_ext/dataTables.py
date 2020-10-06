"""
Directive for using datatables javascript library
"""

import csv

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.util.docutils import SphinxDirective


class data_table(nodes.General, nodes.Element):
    pass


class DataTable(SphinxDirective):

    has_content = True

    def run(self):
        settings = {}

        for content in self.content:
            split_content = content.split(":", 1)
            settings[split_content[0].strip()] = split_content[1].strip()

        node = data_table()
        node.table_id = f'table-{self.env.new_serialno("table")}'
        node.settings = settings

        with open(settings["csv_file"]) as f:
            reader = csv.reader(f)

            for count, row in enumerate(reader):
                if count == 0:
                    node.headers = row
                    node.data = []
                else:
                    node.data.append(row)
        return [node]


def html_visit_output_node(self, node):

    # Build HTML table

    table_string = ""

    table_string += f"<table id='{node.table_id}' class='display'>\n"
    table_string += "\t<thead>\n\t\t<tr>\n"

    for header in node.headers:
        table_string += f"\t\t\t<th>{header}</th>\n"

    table_string += "</tr></thead>\n<tbody>\n"

    for row in node.data:
        table_string += "\t<tr>\n"
        for entry in row:
            try:
                numeric_entry = float(entry)
                entry = f"{numeric_entry:.3f}"
            except ValueError:
                entry = entry

            table_string += f"\t\t\t<td>{entry}</td>\n"
        table_string += "\t</tr>\n"

    table_string += "\t</tbody>"
    table_string += "</table>"

    self.body.append(table_string)


def html_depart_output_node(self, node):

    initialize_table_script = f"""<script>

    $(document).ready( function () {{
            $('#{node.table_id}').DataTable({{"ordering": false, "paging": false}});}} );

                            
    </script><br>"""

    self.body.append(initialize_table_script)


def setup(app):

    app.add_node(
        data_table,
        html=(html_visit_output_node, html_depart_output_node),
    )

    app.add_directive("datatable", DataTable)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
