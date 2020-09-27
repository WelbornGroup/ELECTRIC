from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.util.docutils import SphinxDirective


class view(nodes.General, nodes.Element):
    pass

class MoleculeView(SphinxDirective):

    has_content = True

    def run(self):
        view_id = F'viewport-{self.env.new_serialno("view")}' 
        settings = {}

        for content in self.content:
            split_content = content.split(':', 1)
            settings[split_content[0] ] = split_content[1]

        node = view()
        node.view_id = view_id
        node.settings = settings
        return [node]

def html_visit_output_node(self, node):

    defaults = {
        "data-backgroundcolor": "white",
        "width": "400px",
        "height": "300px",
    }

    if 'data-pdb' not in node.settings and 'data-href' not in node.settings:
        raise KeyError("You must specify a path to a pdb or file to visualize.")
    
    if 'data-pdb' and 'data-href' in node.settings:
        raise ValueError("You should only specify one molecule file to visualize.")

    for k, v in node.settings.items():
        defaults[k] = v.strip()

    source_string = ''

    if 'data-pdb' in defaults:
        source_string = F'data-pdb={defaults["data-pdb"]}'
    elif 'data-href' in defaults:
        source_string = F'data-href={defaults["data-href"]}'

    self.body.append(F"""    
         <center><div style="height: {defaults['height']}; width: {defaults['width']}; position: relative;" class='viewer_3Dmoljs' {source_string} data-backgroundcolor='0xffffff' data-style='stick'></div></center>""")

def html_depart_output_node(self, node):
    pass


def setup(app):

    app.add_node(
        view,
        html=(
            html_visit_output_node,
            html_depart_output_node
        ),
    )

    app.add_directive("moleculeview", MoleculeView)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

