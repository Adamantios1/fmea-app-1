import streamlit as st
import uuid
from anytree import Node
from streamlit_tree_select import tree_select

# Define allowed child node types for each node type
allowed_child_types = {
    'System': ['SubSystem', 'Function'],
    'SubSystem': ['SubSystem', 'Function'],
    'Function': ['Failure'],
    'Failure': ['Effect'],
    'Effect': ['Cause'],
    'Cause': []  # Cause is a leaf node
}

# Function to convert system tree nodes into a list for streamlit-tree-select
def system_node_to_dict(node):
    if not isinstance(node, Node):
        st.write('Error in system_node_to_dict: node is not a Node!')
        st.write('node:', node)
        return {}  # Skip processing if node is not a Node
    label = node.name
    if getattr(node, 'type', None) == 'Effect':
        label += f" (Severity: {node.severity})"
    elif getattr(node, 'type', None) == 'Cause':
        label += f" (Occurrence: {node.occurrence}, Detection: {node.detection})"
    elif getattr(node, 'type', None) == 'Failure':
        label += f" (RPN: {node.rpn})"
    node_dict = {
        'label': label,
        'value': node.node_id  # Use node.node_id
    }
    if node.children:
        node_dict['children'] = [system_node_to_dict(child) for child in node.children]
    return node_dict

def system_tree_to_list(node):
    return [system_node_to_dict(node)]

# Function to find a node by node_id
def find_node_by_id(node, node_id):
    if not isinstance(node, Node):
        st.write('Error in find_node_by_id: node is not a Node!')
        st.write('node:', node)
        return None
    if node.node_id == node_id:
        return node
    for child in node.children:
        result = find_node_by_id(child, node_id)
        if result:
            return result
    return None

# Function to compute RPN for Failure nodes
def compute_rpn(failure_node):
    rpn_list = []
    for effect_node in failure_node.children:
        if getattr(effect_node, 'type', None) == 'Effect':
            severity = effect_node.severity
            for cause_node in effect_node.children:
                if getattr(cause_node, 'type', None) == 'Cause':
                    occurrence = cause_node.occurrence
                    detection = cause_node.detection
                    rpn = severity * occurrence * detection
                    rpn_list.append(rpn)
    if rpn_list:
        failure_node.rpn = max(rpn_list)
    else:
        failure_node.rpn = None

# Initialize session state for the system tree
if 'system_tree' not in st.session_state:
    st.session_state.system_tree = Node("System 1", node_id=str(uuid.uuid4()), type='System')
    st.session_state.selected_node = st.session_state.system_tree

# Sidebar for resetting the application
if st.sidebar.button("Reset Application"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# Sidebar for adding nodes to the System structure
st.sidebar.title("Add Node to System Tree")

node_input = st.sidebar.text_input("Node Name", "")

selected_node = st.session_state.selected_node

if selected_node:
    parent_type = selected_node.type
    allowed_types = allowed_child_types.get(parent_type, [])
    if not allowed_types:
        st.sidebar.write(f"Cannot add child nodes to a '{parent_type}' node.")
else:
    parent_type = None
    allowed_types = ['System']

if allowed_types:
    node_type = st.sidebar.selectbox("Select Node Type", options=allowed_types)
else:
    node_type = None

if st.sidebar.button("Add Node") and node_input and node_type:
    if selected_node and isinstance(selected_node, Node):
        parent_type = selected_node.type
        allowed_types = allowed_child_types.get(parent_type, [])
        if node_type in allowed_types:
            # Add node under selected_node
            new_node = Node(
                node_input,
                parent=selected_node,
                node_id=str(uuid.uuid4()),
                type=node_type
            )
            # Initialize properties
            if node_type == 'Effect':
                new_node.severity = 1
            elif node_type == 'Cause':
                new_node.occurrence = 1
                new_node.detection = 1
            st.session_state.selected_node = new_node
            # Recompute RPN if necessary
            if node_type in ['Effect', 'Cause']:
                failure_node = new_node
                while failure_node and failure_node.type != 'Failure':
                    failure_node = failure_node.parent
                if failure_node:
                    compute_rpn(failure_node)
        else:
            st.sidebar.warning(f"Cannot add a '{node_type}' node under a '{parent_type}' node.")
    else:
        if node_type == 'System':
            # Add node under the root
            new_node = Node(
                node_input,
                parent=st.session_state.system_tree,
                node_id=str(uuid.uuid4()),
                type=node_type
            )
            st.session_state.selected_node = new_node
        else:
            st.sidebar.warning("Please select a node to add under.")

# Display the system tree
system_tree_data = system_tree_to_list(st.session_state.system_tree)

# Display the tree and allow selection
selected = tree_select(
    system_tree_data,
    expand_on_click=True,
    key='tree_select_state'  # Use a different key here to avoid conflict
)

# Update the selected node in session state based on selection
if selected and 'checked' in selected and selected['checked']:
    selected_value = selected['checked'][0]  # Assuming single selection
    selected_node = find_node_by_id(st.session_state.system_tree, selected_value)
    if selected_node:
        st.session_state.selected_node = selected_node
    else:
        st.session_state.selected_node = None
else:
    st.session_state.selected_node = None

# Sidebar for node properties
st.sidebar.title("Properties")

selected_node = st.session_state.selected_node

if selected_node and isinstance(selected_node, Node):
    st.sidebar.subheader(f"Node Properties ({selected_node.type})")
    with st.sidebar.form("node_form"):
        node_name = st.text_input("Name", selected_node.name)
        # Show properties based on node type
        if selected_node.type == 'Effect':
            severity = st.number_input("Severity (1-10)", min_value=1, max_value=10,
                                       value=getattr(selected_node, 'severity', 1))
        elif selected_node.type == 'Cause':
            occurrence = st.number_input("Occurrence (1-10)", min_value=1, max_value=10,
                                         value=getattr(selected_node, 'occurrence', 1))
            detection = st.number_input("Detection (1-10)", min_value=1, max_value=10,
                                        value=getattr(selected_node, 'detection', 1))
        update_button = st.form_submit_button("Update")
        if update_button:
            selected_node.name = node_name
            if selected_node.type == 'Effect':
                selected_node.severity = severity
            elif selected_node.type == 'Cause':
                selected_node.occurrence = occurrence
                selected_node.detection = detection
            # Recompute RPN if necessary
            if selected_node.type in ['Effect', 'Cause']:
                failure_node = selected_node
                while failure_node and failure_node.type != 'Failure':
                    failure_node = failure_node.parent
                if failure_node:
                    compute_rpn(failure_node)
else:
    st.sidebar.write("Select a node to view or edit properties.")
