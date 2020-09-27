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
        "data-style": "stick"
    }

    if 'data-pdb' not in node.settings and 'data-href' not in node.settings:
        raise KeyError("You must specify a path to a pdb or file to visualize.")
    
    if 'data-pdb' and 'data-href' in node.settings:
        raise ValueError("You should only specify one molecule file to visualize.")

    for k, v in node.settings.items():
        k = k.strip()
        defaults[k] = v.strip()

    source_string = ''

    if 'data-pdb' in defaults:
        source_string = F'data-pdb={defaults["data-pdb"]}'
    elif 'data-href' in defaults:
        source_string = F'data-href={defaults["data-href"]}'

    # Set data styles
    data_style = ''

    # Process extra styles
    style_keys = [k for k in defaults.keys() if 'style' in k]
    select_keys = [k for k in defaults.keys() if 'select' in k]
    
    for i in range(len(style_keys)):
        style_key = style_keys[i]
        data_style += F" {style_key}={defaults[style_key]} "
    
    for i in range(len(select_keys)):
        select_key = select_keys[i]
        data_style += F" {select_key}={defaults[select_key]} "

    show_string = F'<center><div style="height: {defaults["height"]}; width: {defaults["width"]}; position: relative;" class="viewer_3Dmoljs" {source_string} data-backgroundcolor="{defaults["data-backgroundcolor"]}" {data_style}></div></center>'

    self.body.append(show_string)

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

