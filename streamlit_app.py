import streamlit as st

st.title("iFMEA")
st.write(
    "Let's start building!"
)
# import streamlit as st
import pandas as pd
from anytree import Node, PreOrderIter
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Function to convert anytree nodes into a flat list for AgGrid with specified levels
def flatten_tree(node):
    def _flatten(node, level=0):
        result = [{"name": f"{'— ' * level}{node.name}", "level": level}]
        for child in node.children:
            result.extend(_flatten(child, level + 1))
        return result
    return _flatten(node)

# Initialize session state for trees if not set
if 'system_tree' not in st.session_state:
    st.session_state.system_tree = Node("System 1")
    st.session_state.fmea_trees = {}

if 'selected_system_node' not in st.session_state:
    st.session_state.selected_system_node = None

# Sidebar for adding nodes to the System structure
st.sidebar.title("System Structure")
system_input = st.sidebar.text_input("Add System/Component", "")
add_type = st.sidebar.radio("Add as:", ["Same Level", "Next Level"])

# Add to System Tree
if st.sidebar.button("Add to System Tree") and system_input:
    selected_node = st.session_state.selected_system_node

    if selected_node:
        if add_type == "Next Level":
            # Add the new node as a child of the selected node
            new_node = Node(system_input)
            new_node.parent = selected_node
        elif add_type == "Same Level" and selected_node.parent:
            # Add the new node as a sibling of the selected node
            parent_node = selected_node.parent
            new_node = Node(system_input)
            siblings = list(parent_node.children)
            index = siblings.index(selected_node) + 1
            siblings.insert(index, new_node)
            parent_node.children = siblings
    else:
        # If no node is selected, add it as a child of the root node
        new_node = Node(system_input, parent=st.session_state.system_tree)

    # Update the selected node to the new node
    st.session_state.selected_system_node = new_node

# Create columns for side-by-side layout
col1, col2 = st.columns(2)

# Display the system structure in the first column
with col1:
    st.subheader("System Structure")
    system_tree_data = flatten_tree(st.session_state.system_tree)

    # Create DataFrame from flattened tree data
    df_system_tree = pd.DataFrame(system_tree_data)

    # Configure AgGrid for displaying the tree
    gb = GridOptionsBuilder.from_dataframe(df_system_tree)
    gb.configure_selection(selection_mode='single', use_checkbox=True)
    gb.configure_column("name", header_name="System/Component", sortable=False)
    gb.configure_column("level", header_name="Level", hide=True)
    grid_options = gb.build()

    # Display the tree structure
    selected_system = AgGrid(
        df_system_tree,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=300,
        fit_columns_on_grid_load=True
    )

    # Update the selected system node based on AgGrid selection
    selected_rows = selected_system.get('selected_rows', [])
    if isinstance(selected_rows, list) and len(selected_rows) > 0:
        selected_node_name = selected_rows[0].get('name', None).replace('— ', '').strip()
        if selected_node_name:
            for node in PreOrderIter(st.session_state.system_tree):
                if node.name == selected_node_name:
                    st.session_state.selected_system_node = node
                    break

# Input form for selected nodes in the system structure
st.sidebar.title("Properties")
if st.session_state.selected_system_node:
    with st.sidebar.form("system_form"):
        node_name = st.text_input("Name", st.session_state.selected_system_node.name)
        node_description = st.text_area("Description", "")
        update_button = st.form_submit_button("Update")
        if update_button:
            st.session_state.selected_system_node.name = node_name
