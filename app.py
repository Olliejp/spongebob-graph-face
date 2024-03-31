import streamlit as st
from config_ import category_tree
import igraph as ig
import plotly.graph_objects as go

#st.markdown("""
#    <style>
#        #MainMenu {visibility: hidden;}
#        .stDeployButton {display:none;}
#        footer {visibility: hidden;}
#        #stDecoration {display:none;} 
#        .st-emotion-cache-z5fcl4 {
#        width: 100%;
#        padding: 3rem 3rem 10rem;
#        min-width: auto;
#        max-width: initial;
#        }
#        #GithubIcon {visibility: hidden;}
#        .st-emotion-cache-zq5wmm {visibility: hidden;}
#    </style>
#""", unsafe_allow_html=True)

st.set_page_config(layout="wide")
st.set_page_config(menu_items=None)

def build_full_path_for_node(node, tree):
    path = []

    # Recursive function to find the path
    def find_path(current_node, current_tree, current_path):
        for key, subtree in current_tree.items():
            if key == current_node:
                return current_path + [key]
            elif isinstance(subtree, dict):
                found_path = find_path(current_node, subtree, current_path + [key])
                if found_path:
                    return found_path
        return None  # Node not found in this branch

    # Start the recursive search from the root of the tree
    full_path = find_path(node, tree, [])
    if full_path:
        return ' > '.join(full_path)
    else:
        return 'Node not found'

def calculate_node_depths(tree, path=[]):
    """Recursively calculate the depth of each node in the hierarchy."""
    depths = {}
    for node, children in tree.items():
        current_path = path + [node]
        depths[node] = len(path)
        if isinstance(children, dict):
            child_depths = calculate_node_depths(children, current_path)
            depths.update(child_depths)
    return depths

#def build_custom_layout(g, labels, node_depths):
#    """Build a custom layout for the graph based on node depths."""
#    max_depth = max(node_depths.values())
#    y_positions = {depth: depth * 10 for depth in range(max_depth + 1)} 
    
#    layout = {}
#    for label in labels:
#        depth = node_depths[label]
#        x = depth  # Use depth for x position
#        y = y_positions[depth]
#        y_positions[depth] += 1 
#        layout[label] = (x, y)
#    return layout

def build_custom_layout(g, labels, node_depths):
    """Build a custom layout for the graph based on node depths."""
    max_depth = max(node_depths.values())
    # Increase the base vertical separation to create more space between nodes
    base_vertical_separation = 20  # Adjust this value as needed to increase vertical separation

    y_positions = {depth: depth * base_vertical_separation for depth in range(max_depth + 1)}

    layout = {}
    for label in labels:
        depth = node_depths[label]
        x = depth  # Use depth for x position
        y = y_positions[depth]
        # Increase the vertical position increment to add more space between nodes at the same depth
        y_positions[depth] += base_vertical_separation  # Increase this increment if more space is needed
        layout[label] = (x, y)
    return layout


def build_path_graph_with_branching(category_tree, path):
    g = ig.Graph()
    labels = []

    def add_vertex(node):
        if node not in labels:
            g.add_vertex(node)
            labels.append(node)

    def add_edge(parent, child):
        if not g.are_connected(parent, child):
            g.add_edge(parent, child)

    # Recursive function to add all nodes under the current path
    def add_branch(parent, subtree):
        if isinstance(subtree, dict):
            for child, grandchild in subtree.items():
                add_vertex(child)
                add_edge(parent, child)
                add_branch(child, grandchild)

    # Trace and add the path from the root to the current selection
    for i, node in enumerate(path):
        add_vertex(node)
        if i > 0:
            add_edge(path[i - 1], node)

    # If the path ends in a selectable node, branch out from there
    if path:
        current_node = path[-1]
        subtree = get_subdict_from_path(category_tree, path[:-1])
        if current_node in subtree:
            add_branch(current_node, subtree[current_node])

    return g, labels

# Function to extract the keys at any level in the nested dictionary
def get_keys_at_level(d, path):
    for key in path:
        d = d.get(key, {})
    return list(d.keys())

# Function to navigate and extract the sub-dictionary based on the selected path
def get_subdict_from_path(d, path):
    for key in path:
        d = d.get(key, {})
    return d

# Function to initialize or reset session state
def initialize_or_reset_session_state():
    st.session_state['selected_path'] = []
    st.session_state['dropdown_selections'] = [""]
    st.session_state['category_tree'] = category_tree

# Initialize session state to store the selected path, dropdown selections, and the full category_tree
if 'selected_path' not in st.session_state or 'dropdown_selections' not in st.session_state or 'category_tree' not in st.session_state:
    initialize_or_reset_session_state()

# Reset functionality
if st.button("Reset"):
    initialize_or_reset_session_state()
    st.experimental_rerun()

# Top level categories
top_level_keys = [""] + list(st.session_state['category_tree'].keys())
selected_level = st.selectbox('Select category', top_level_keys, index=0, key='level_0')

# Check if a top-level category has been selected and update session state accordingly
if selected_level:
    if len(st.session_state['dropdown_selections']) < 1 or st.session_state['dropdown_selections'][0] != selected_level:
        st.session_state['dropdown_selections'] = [selected_level]
    st.session_state['selected_path'] = [selected_level]
else:
    st.session_state['selected_path'] = []
    st.session_state['dropdown_selections'] = [""]

# Dynamically create dropdowns for each level based on the previous selection, if a selection has been made
if selected_level:
    current_dict = st.session_state['category_tree'][selected_level]
    level = 1
    while current_dict:
        keys = [""] + list(current_dict.keys())
        if not keys:
            break
        selected_key = st.selectbox(f'Select subcategory at level {level}', keys, index=0, key=f'level_{level}')
        
        # Break the loop if no subcategory is selected
        if not selected_key:
            break
        
        # Update or append the selection to the session state
        if len(st.session_state['dropdown_selections']) <= level:
            st.session_state['dropdown_selections'].append(selected_key)
        else:
            st.session_state['dropdown_selections'][level] = selected_key
        
        # Update the path based on the selection
        st.session_state['selected_path'].append(selected_key)
        
        current_dict = current_dict.get(selected_key, {})
        level += 1

# Display the selected path if a valid selection is made beyond the top-level
if len(st.session_state['selected_path']) > 1:
    st.write('Selected Path:', ' > '.join(st.session_state['selected_path']))

node_depths = calculate_node_depths(category_tree)

g, labels = build_path_graph_with_branching(category_tree, st.session_state['selected_path'])

# Only proceed if the graph has vertices
if len(g.vs) > 0:
    custom_layout = build_custom_layout(g, labels, node_depths)
    
    # Convert custom layout to plotly-compatible format
    Xn = [custom_layout[label][0] for label in labels]  # x positions for nodes
    Yn = [-custom_layout[label][1] for label in labels]  # y positions for nodes (negative for vertical alignment from top)

    Xe = []
    Ye = []
    for edge in g.es:
        source, target = edge.tuple
        source_label = g.vs[source]['name']
        target_label = g.vs[target]['name']
        Xe += [custom_layout[source_label][0], custom_layout[target_label][0], None]
        Ye += [-custom_layout[source_label][1], -custom_layout[target_label][1], None]  # Negative for vertical alignment

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=Xe, y=Ye, mode='lines', line=dict(color='rgb(210,210,210)', width=1), hoverinfo='none'))
    #fig.add_trace(go.Scatter(x=Xn, y=Yn, mode='markers', name='', marker=dict(symbol='circle-dot', size=18, color='#6175c1', line=dict(color='rgb(50,50,50)', width=1)), text=labels, hoverinfo='text', opacity=0.8))

    # Define a color palette for the nodes at different depths
    #color_palette = ['#FF5733', '#33BEFF', '#50C878', '#FFD700', '#FF69B4']  # Add more colors as needed
    colour_palette = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']

    # Assign colors to nodes based on their depth
    node_colors = [colour_palette[node_depths[label] % len(colour_palette)] for label in labels]

    # Create a trace for each level to show up in the legend (use a dummy X and Y)
    #for depth in range(max(node_depths.values()) + 1):
    #    fig.add_trace(go.Scatter(
    #        x=[None], y=[None],
    #        mode='markers',
    #        marker=dict(size=10, color=color_palette[depth % len(color_palette)]),
    #        name=f'Category Level {depth+1}'
    #    ))

    # Hover text with full paths
    hover_texts = []
    for label in labels:
        full_path = build_full_path_for_node(label, category_tree)
        level = node_depths[label]
        #hover_text = f"{full_path} <br> Level {level} {label}"
        hover_text = f"Level: {level} <br><br> {full_path}"
        hover_texts.append(hover_text)

    # Plot nodes with the assigned colors
    fig.add_trace(go.Scatter(
        x=Xn, y=Yn, mode='markers', 
        marker=dict(symbol='circle', size=25, color=node_colors, line=dict(color='rgb(50,50,50)', width=0.5)),
        #text=[f"Level {node_depths[label]+1}: {label}" for label in labels],  # Modify this line for tooltip
        text=hover_texts,
        hoverinfo='text', 
        hoverlabel=dict(font=dict(color='black', size=14)),
        opacity=0.8
    ))
    
    # Corrected Annotations
    #annotations = []
    #for label in labels:
    #    if label in custom_layout:
    #        pos = custom_layout[label]
    #        annotations.append(dict(
    #            text=label,
    #            x=pos[0],
    #            y=-pos[1],  # Assuming you still want to invert y for visual reasons
    #            xref='x1', yref='y1',
    #            font=dict(color='rgb(250,250,250)', size=10),
    #            showarrow=False
    #        ))

    # Annotations with level numbers
    annotations = []
    for label in labels:
        if label in custom_layout:
            pos = custom_layout[label]
            level_number = node_depths[label]
            annotations.append(dict(
                text=f"L{level_number}",  # This sets the text as 'L' followed by the level number
                x=pos[0],
                y=-pos[1],  # Assuming you still want to invert y for visual reasons
                xref='x1', yref='y1',
                #font=dict(color='rgb(250,250,250)', size=12),  # Adjust color and size as needed
                font=dict(color='black', size=12),  # Adjust color and size as needed
                showarrow=False
            ))


    fig.update_layout(title='Category Tree',
                    annotations=annotations,
                    font_size=12,
                    showlegend=False,
                    xaxis=dict(showline=False, zeroline=False, showgrid=False, showticklabels=False),
                    yaxis=dict(showline=False, zeroline=False, showgrid=False, showticklabels=False),
                    margin=dict(l=40, r=40, b=80, t=100),
                    hovermode='closest',
                    height=700,
                    plot_bgcolor='rgb(248,248,248)')

    st.plotly_chart(fig, use_container_width=True, config= {'displaylogo': False})
else:
    # Display a message or an empty figure if the graph is empty
    st.write("No selection made")

