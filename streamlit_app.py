import streamlit as st

st.title("iFMEA")
st.write(
    "Let's start building!"
)
# import streamlit as st
import uuid
from anytree import Node
from streamlit_tree_select import tree_select

# Function to convert anytree nodes into a list for streamlit-tree-select
def anytree_to_list(node):
    def node_to_dict(node):
        node_dict = {
            'label': node.name,
            'value': node.id  # Use unique id
        }
        if node.children:
            node_dict['children'] = [node_to_dict(child) for child in node.children]
        return node_dict
    return [node_to_dict(node)]  # The root node(s) should be in a list

# Initialize session state for trees if not set
if 'system_tree' not in st.session_state:
    # Assign a unique ID to the root node
    st.session_state.system_tree = Node("System 1", id=str(uuid.uuid4()))
    st.session_state.selected_system_node = st.session_state.system_tree

# Initialize session state for expanded nodes
if 'expanded_nodes' not in st.session_state:
    st.session_state.expanded_nodes = []  # List to keep track of expanded node IDs

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
            new_node = Node(system_input, parent=selected_node, id=str(uuid.uuid4()))
            st.session_state.selected_system_node = new_node
        elif add_type == "Same Level":
            if selected_node.parent:
                # Add the new node as a sibling of the selected node
                new_node = Node(system_input, parent=selected_node.parent, id=str(uuid.uuid4()))
                st.session_state.selected_system_node = new_node
            else:
                # Selected node is root node, cannot add sibling
                st.warning("Cannot add a sibling to the root node.")
                new_node = None
    else:
        # If no node is selected, add it as a child of the root node
        new_node = Node(system_input, parent=st.session_state.system_tree, id=str(uuid.uuid4()))
        st.session_state.selected_system_node = new_node

    # Optionally, expand the parent node of the new node
    if new_node and new_node.parent:
        parent_id = new_node.parent.id
        if parent_id not in st.session_state.expanded_nodes:
            st.session_state.expanded_nodes.append(parent_id)

# Convert the anytree to a list for display
tree_data = anytree_to_list(st.session_state.system_tree)

# Display the tree and allow selection
selected = tree_select(
    tree_data,
    expand_on_click=True,
    expanded=st.session_state.expanded_nodes  # Pass the expanded nodes
)

# Update the expanded nodes in session state
if selected and 'expanded' in selected:
    st.session_state.expanded_nodes = selected['expanded']

st.write('You selected:', selected)

# Update the selected node in session state based on selection
def find_node_by_id(node, node_id):
    if node.id == node_id:
        return node
    for child in node.children:
        result = find_node_by_id(child, node_id)
        if result:
            return result
    return None

if selected and 'checked' in selected and selected['checked']:
    selected_value = selected['checked'][0]  # Get the first selected node's value (id)
    node = find_node_by_id(st.session_state.system_tree, selected_value)
    if node:
        st.session_state.selected_system_node = node
else:
    st.session_state.selected_system_node = None

# Sidebar for node properties
st.sidebar.title("Properties")
if st.session_state.selected_system_node:
    with st.sidebar.form("system_form"):
        node_name = st.text_input("Name", st.session_state.selected_system_node.name)
        node_description = st.text_area("Description", "")
        update_button = st.form_submit_button("Update")
        if update_button:
            st.session_state.selected_system_node.name = node_name
