import streamlit as st

st.title("iFMEA")
st.write(
    "Let's start building!"
)
# import streamlit as st
import pandas as pd
from anytree import Node
from anytree.exporter import JsonExporter
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Function to convert anytree nodes into a flat list for AgGrid
def flatten_tree(node, level=0):
    result = [{"name": node.name, "level": level}]
    for child in node.children:
        result.extend(flatten_tree(child, level + 1))
    return result

# Initialize session state for trees if not set
if 'system_tree' not in st.session_state:
    st.session_state.system_tree = Node("System")
    st.session_state.fmea_trees = {}

if 'selected_system_node' not in st.session_state:
    st.session_state.selected_system_node = None

if 'selected_fmea_node' not in st.session_state:
    st.session_state.selected_fmea_node = None

# Sidebar for adding nodes to the System structure
st.sidebar.title("System Structure")
system_input = st.sidebar.text_input("Add System/Component", "")
if st.sidebar.button("Add to System Tree"):
    parent_node = st.session_state.selected_system_node or st.session_state.system_tree
    new_node = Node(system_input, parent=parent_node)
    st.session_state.selected_system_node = new_node

# Display the system structure using AgGrid
st.subheader("System Structure")
system_tree_data = flatten_tree(st.session_state.system_tree)

# Create DataFrame from flattened tree data
df_system_tree = pd.DataFrame(system_tree_data)

# Configure AgGrid for displaying the tree
gb = GridOptionsBuilder.from_dataframe(df_system_tree)
gb.configure_selection(selection_mode='single', use_checkbox=True)
gb.configure_column("name", header_name="System/Component")
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
if len(selected_system['selected_rows']) > 0:
    selected_node_name = selected_system['selected_rows'][0]['name']
    for node in st.session_state.system_tree.descendants:
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

# FMEA Tree based on selected system node
if st.session_state.selected_system_node:
    selected_system = st.session_state.selected_system_node
    fmea_tree = st.session_state.fmea_trees.get(
        selected_system.name, Node(f"{selected_system.name}_Function")
    )
    st.session_state.fmea_trees[selected_system.name] = fmea_tree

    # Sidebar for adding nodes to the FMEA tree
    with st.sidebar.form("fmea_form"):
        fmea_input = st.text_input("Add FMEA Node", "")
        fmea_type = st.selectbox("Type", ["Function", "Failure", "Effect", "Cause"])
        add_fmea_node = st.form_submit_button("Add to FMEA Tree")

        if add_fmea_node and fmea_input:
            parent_node = st.session_state.selected_fmea_node or fmea_tree
            new_fmea_node = Node(f"{fmea_type}: {fmea_input}", parent=parent_node)
            st.session_state.selected_fmea_node = new_fmea_node

    # Convert FMEA tree to flat list for AgGrid
    fmea_tree_data = flatten_tree(fmea_tree)
    df_fmea_tree = pd.DataFrame(fmea_tree_data)

    # Configure AgGrid for FMEA tree
    gb_fmea = GridOptionsBuilder.from_dataframe(df_fmea_tree)
    gb_fmea.configure_selection(selection_mode='single', use_checkbox=True)
    gb_fmea.configure_column("name", header_name="FMEA Node")
    gb_fmea.configure_column("level", header_name="Level", hide=True)
    fmea_grid_options = gb_fmea.build()

    # Display the FMEA tree
    st.subheader("FMEA Structure")
    fmea_grid = AgGrid(
        df_fmea_tree,
        gridOptions=fmea_grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=300,
        fit_columns_on_grid_load=True
    )

    # Update the selected FMEA node based on AgGrid selection
    if len(fmea_grid['selected_rows']) > 0:
        selected_fmea_node_name = fmea_grid['selected_rows'][0]['name']
        for node in fmea_tree.descendants:
            if node.name == selected_fmea_node_name:
                st.session_state.selected_fmea_node = node
                break

    # Input form for selected nodes in the FMEA structure
    if st.session_state.selected_fmea_node:
        fmea_node = st.session_state.selected_fmea_node

        with st.sidebar.form("fmea_properties_form"):
            node_name = st.text_input("Name", fmea_node.name.split(": ")[-1])
            node_description = st.text_area("Description", "")
            severity = occurrence = detection = None
            if "Effect" in fmea_node.name:
                severity = st.slider("Severity (1-10)", min_value=1, max_value=10)
            if "Cause" in fmea_node.name:
                occurrence = st.slider("Occurrence (1-10)", min_value=1, max_value=10)
                detection = st.slider("Detection (1-10)", min_value=1, max_value=10)
            update_fmea = st.form_submit_button("Update")

            if update_fmea:
                fmea_node.name = f"{fmea_type}: {node_name}"
                if severity:
                    fmea_node.name += f" (Severity: {severity})"
                if occurrence and detection:
                    rpn = severity * occurrence * detection if severity else 1
                    fmea_node.name += f" (Occurrence: {occurrence}, Detection: {detection}, RPN: {rpn})"
                
                st.success("FMEA node updated")