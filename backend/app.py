from tree import Node
from lexicon import Feature, is_phrase
from operations import merge, adjoin, agree, internal_merge
from validator import validate_derivation

from flask import Flask, jsonify, request
from flask_cors import CORS
import re

app = Flask(__name__)                                                   # Initializing the application
CORS(app)                                                               # Allow Cross-Origin Resource Sharing

@app.route('/api/status', methods = ['GET'])
def check_status():
    """
    Assuring connection to backend.

    Returns:
        JSON: A json file assuring that the backend is connected.
    """
    return jsonify({
        "status": "online",
        "message": "The Minimalist Validator API is working perfectly"
    })

# Turning the raw feature string into a Feature object
def parse_feature(raw_feat: str) -> Feature:
    """
    Parsing the string feature into a Feature object.
    
    Args:
        raw_feat (str): The raw feature string.
    
    Returns:
        Feature: The parsed Feature object.
    """

    raw = raw_feat.strip()
    
    # Safely evaluating the Greek phi symbol
    if raw.startswith("uφ:") or raw.startswith("uphi:"):
        # This is an uninterpretable phi feature with value.
        val = raw.split(":")[1]
        feat = Feature(type="phi", val=val, interpretable=False)
        feat.checked = True
        return feat
        
    if raw == "uφ" or raw == "uphi":
        # This is an uninterpretable phi feature that needs value.
        return Feature(type="phi", val=None, interpretable=False)
    if raw.lower() == "ucase":
        # This is an uninterpretable case feature that needs value.
        return Feature(type="case", val=None, interpretable=False)
    if raw.lower().startswith("case:"):
        feat = Feature(type="case", val=raw.lower().split(":")[1].strip(), interpretable=False)
        feat.checked = True
        return feat
        
    if raw.startswith("u"):
        # Fallback option for uF: the feature is a selection feature
        return Feature(type="select", val=raw[1:], interpretable=False)

    # Fallback option: The feature is interpretable (phi-feature).        
    return Feature(type="phi", val=raw, interpretable=True)

def find_target(node: Node):
    """
    Recursively searching for a node with a True 'is_target' argument within the node's domain.

    Args:
        node (Node): The node whose domain the function traverses (in Pre-Order) for a target node.
    """

    if getattr(node, 'is_target', False):   # Using 'getattr' function to avoid raising exception in case 'is_target' attribute does not exist.
        return node
    if node.left:
        found = find_target(node.left)
        if found:
            return found
    if node.right:
        found = find_target(node.right)
        if found:
            return found
    return None
    
def can_merge(head: Node, comp: Node) -> bool:
    """
    Checking if a node can select another one for merging, according to minimalist theory constraints.

    Args:
        head (Node): The node with a category uninterpreted feature waiting to be checked.
        comp (Node): The potential complement node, whose category is checked against the head's request.

    Returns:
        bool: True is the complement's category satisfies the head's selection feature, False otherwise.
    """

    reqs = [f for f in head.features if f.type == "select" and f.is_active()]
    cats = [f for f in comp.features if f.type == "category"]
    if reqs and cats:
        return reqs[0].val == cats[0].val
    return False

def build_tree_from_json(node_dict: dict) -> Node:
    """
    Recursively constructing the syntactic tree from its representation in json format.

    Args:
        node_dict (dict): A recursive dictionary representing the visual tree, where each node has the following keys:
            -'type' (Either 'terminal' or 'non-terminal')
            -'text' (For terminal nodes only, the text containing their category and features)
            -'label' (For non-terminal nodes only, the text containing their category, with no features)
            -'left' (For non-terminal nodes, a dict representing the left subtree of the node)
            -'right' (For non-terminal nodes, a dict representing the right subtree of the node)
            -'isTrace' (True if the node is marked as a trace, False otherwise)
            -'selected' (True is the node is currently highlighted by the user (specifically for the Move operation), False otherwise)
            'id' (A numerical ID for necessary operations)
    
    Returns:
        Node: The root of the constructed syntactic tree.

    Raises:
        ValueError: If the structure of the tree is impossible by syntactic standard (Two subtrees cannot theoretically combine under minimalist theory constraints).
    """

    if node_dict.get('type') == 'terminal':
        # Base case: The tree consists of a single node.
        node = parse_node(node_dict['text'])
        
    if node_dict.get('type') == 'non-terminal':
        # Recursively constructing the two child subtrees, before attempting to combine them.
        left_child = build_tree_from_json(node_dict['left'])
        right_child = build_tree_from_json(node_dict['right'])
        expected_label = node_dict.get('label', '') # This is the expected label of the parent node, to be compared to the result of combining methods.
        
        # Checking if the combining operation can be External Merge.
        if can_merge(left_child, right_child):
            node = merge(head=left_child, complement=right_child)
        elif can_merge(right_child, left_child):
            node = merge(head=right_child, complement=left_child)
            # In case of merges where the head is to the right (e.g., DP merging with vP where the head is v), hardcoding the children directionality to preserve visual integrity.
            node.left = left_child
            node.right = right_child
        else:
            # Internal Merge (Move) or Adjunction.
            # Finding the child that matches the expected label, then creating the parent node with its projected features, with no checkings.
            if expected_label == right_child.label:
                node = Node(features=list(right_child.features), left=left_child, right=right_child, label=expected_label)
            elif expected_label == left_child.label:
                node = Node(features=list(left_child.features), left=left_child, right=right_child, label=expected_label)
            else:
                raise ValueError(f"Cannot structurally combine '{left_child.label}' and '{right_child.label}'")
            
            left_child.parent = node
            right_child.parent = node
            
        # Handle structural traces using our boolean property
        if node_dict.get('isTrace', False):
            node.is_trace = True
            node.features = [f for f in node.features if f.type == "category"]
            
    node.node_id = node_dict.get('id')
    node.is_target = node_dict.get('selected', False)
    return node

@app.route('/api/validate', methods = ['POST'])
def validate_workspace():
    """
    Validating the derivation tree as gotten from the frontend.

    Returns:
        JSON: A json object describing the result of the operation (error os success) and the result of the validation (converges or fails at LF)
    """
    # Receiving the data and extracting the items for the tree
    payload = request.get_json()
    tree_data = payload.get('tree')

    if not tree_data:
        return jsonify({
            "status": "error",
            "message": "CRASH: the derivation board is empty"
        }), 400
    try:
        # Attempting to build the tree and and validating the derivation
        derived_root = build_tree_from_json(tree_data)
        converges, crash_log = validate_derivation(derived_root)

        if converges:
            message = "SUCCESS: The derivation converges at Logical Form. All uninterpretable features are checked."
        else:
            message = f"FAILURE: The derivation crashed at LF. Uninterpretable features survived. Survived features: {crash_log}"

        return jsonify({
            "status": "success",
            "message": message,
            "converged": converges
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"CRASH: {str(e)}"
        }), 400

def parse_node(item_text: str) -> Node:
    """
    Parsing the text of a (terminal) node using regular expression logic into a Node object fit to syntactic operations.

    Args:
        item_text (str): The text on a terminal node, with its category and features.
    
    Returns:
        Node: The node object with the features of the input text, after parsing.
    
    Raises:
        ValueError: If the text is malformed in terms of regex expected form of Node representation.
    """
    if "_t" in item_text:   # This is a trace
        base_label = item_text.split('_')[0].strip()
        cat_val = base_label[:-1] if is_phrase(base_label) else base_label
        cat_feat = Feature(type="category", val=cat_val, interpretable=True)
        return Node(features=[cat_feat], label = item_text.strip())

    match = re.match(r"^([a-zA-Z]+)\s*\[(.*)\]$", item_text.strip()) # Attempting to get capture groups for the label and features, based on the expected regex form.
    if not match:
        raise ValueError(f"Lexical analysis failed, '{item_text}' is malformed")
    
    label = match.group(1)
    raw_feats = [f.strip() for f in match.group(2).split(',') if f.strip()]
    node_features = [parse_feature(f) for f in raw_feats]
    cat_val = label[:-1] if is_phrase(label) else label                 # Turning phrases (ending with P) back to their heads (excluding P itself)
    node_features.insert(0, Feature(type =  "category", val = cat_val, interpretable = True))   # Creating the category feature (from the label outside the [])

    return Node(features = node_features, label = label)
    
@app.route('/api/merge', methods = ['POST'])
def execute_merge():
    """
    Executing the Merge operation using data from the frontend.

    Returns:
        JSON: A json object describing the result of the operation, with the resulting label of the parent node in case of success.
    """
    # Receiving the data and extracting the items for merging.
    payload = request.get_json()
    items = payload.get('items', [])

    if len(items) != 2: # Merge must occur between exactly two items.
        return jsonify({
            "status": "error",
            "messgage": "CRASH: merge requires exactly two items"
        }), 400

    # Trying to build the two subtrees to be merged together.
    try:
        item1 = build_tree_from_json(items[0])
        item2 = build_tree_from_json(items[1])

        if can_merge(head = item2, comp = item1):
            merged_node = merge(head = item2, complement = item1)
        else:
            merged_node = merge(head = item1, complement = item2)

        return jsonify({
            "status": "success",
            "message": f"MERGE SUCCESS: Formed [{merged_node.label} {item1.label} {item2.label}]",
            "parent_label": merged_node.label
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"CRASH: {str(e)}"
        }), 400

@app.route('/api/adjoin', methods = ['POST'])
def execute_adjoin():
    """
    Executing the Adjoin operation using data from the frontend.
    
    Returns:
        JSON: A json object describing the result of the operation, with the resulting label of the parent node in case of success.

    Raises:
        ValueError: If the two nodes in the data are not fit to be adjoined together.
    """
    
    # Receiving the data and extracting the items for adjoining.
    payload = request.get_json()
    items = payload.get('items', [])
    if len(items) != 2: # Adjoin must occur between exactly two nodes.
        return jsonify({"status": "error", "message": "CRASH: Adjoin requires exactly two items"}), 400
        
    try:
        left_node = build_tree_from_json(items[0])
        right_node = build_tree_from_json(items[1])
        
        # Parsing te base categories for projection.
        base_left = left_node.label[:-1] if is_phrase(left_node.label) else left_node.label
        base_right = right_node.label[:-1] if is_phrase(right_node.label) else right_node.label

        # Deduce the Target vs Adjunct based on standard linguistic categories
        adjunct_categories = ["Adv", "A", "P"]
        
        if base_right in adjunct_categories and base_left not in adjunct_categories:
            target = left_node   # Right-Adjunction (e.g., VP + PP)
            adjunct = right_node
        elif base_left in adjunct_categories and base_right not in adjunct_categories:
            target = right_node  # Left-Adjunction (e.g., Adv + vP)
            adjunct = left_node
        else:
            raise ValueError(f"ADJOIN CRASH: Cannot adjoin {base_left} and {base_right}. At lease one node must be a valid adjunct ({', '.join(adjunct_categories)}).")

        # Automatically projecting the adjunct node to a phrase node if necessary.
        if not is_phrase(adjunct.label):
            proj_label = adjunct.label+"P"
            new_adjunct = Node(features=list(adjunct.features), left=adjunct, label=proj_label)
            adjunct.parent = new_adjunct

            if adjunct == right_node:
                right_node = new_adjunct
            else:
                left_node = new_adjunct

        # Performing the adjoin and returning a json object containing the new parent node.
        adjoined_node = adjoin(target=target, left_node=left_node, right_node=right_node)
        
        return jsonify({
            "status": "success",
            "message": f"ADJOIN SUCCESS: Formed two-segment category [{adjoined_node.label}]",
            "parent_label": adjoined_node.label
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": f"CRASH: {str(e)}"}), 400

    
@app.route('/api/agree', methods=['POST'])
def execute_agree():
    """
    Executing the Agree operation using data from the frontend.
            
    Returns:
        JSON: A json object containing a status report, a message, and the updated text on the probe (including its updated features) and the specific node the probe found (for UI purposes).
    """

    payload = request.get_json()
    tree_data = payload.get('tree')
    if not tree_data:
        return jsonify({"status": "error", "message": "CRASH: No tree provided"}), 400

    try:
        selected_node = build_tree_from_json(tree_data)
        probe_node = selected_node.left if not selected_node.is_terminal() else selected_node

        def format_node_text(node):
            g_feats = []
            for f in node.features:
                if f.type == "category": continue
                if f.type == "case":
                    if f.type == "case":
                        g_feats.append(f"case:{f.val.upper()}" if f.checked else "ucase")
                elif f.type == "phi" and not f.interpretable:
                    g_feats.append(f"uφ:{f.val}" if f.val else "uφ")
                elif not f.interpretable:
                    g_feats.append(f"u{f.val}")
                else:
                    g_feats.append(f.val)
            return f"{node.label} [{', '.join(g_feats)}]"

        # 1. State Pre-Agree: Map texts by ID
        pre_state = {n.node_id: format_node_text(n) for n in selected_node.get_descendants() if n.node_id}

        # 2. Execute theoretical operation
        goals_found = agree(probe=probe_node)

        # 3. State Post-Agree: Compare texts by ID and collect updates
        updates = []
        for n in selected_node.get_descendants():
            if not n.node_id: continue
            new_text = format_node_text(n)
            if pre_state.get(n.node_id) != new_text:
                updates.append({
                    "id": n.node_id,
                    "text": new_text
                })

        return jsonify({
            "status": "success",
            "message": f"AGREE SUCCESS: Probe '{probe_node.label}' successfully checked its features",
            "updates": updates
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": f"CRASH: {str(e)}"}), 400

@app.route('/api/move', methods=['POST'])
def execute_move():
    """
    Executing the internal merge (move) operation using data from the frontend.

    Returns:
        JSON: A json object containing a status report, a message and the new parent label of the move operation in case of success.
    """
    payload = request.get_json()
    tree_data = payload.get('tree')

    if not tree_data:
        return jsonify({
            "status": "error",
            "message": "CRASH: No tree provided for Move operation"
        }), 400
    
    try:
        root_node = build_tree_from_json(tree_data)
        goal_node = find_target(root_node)
        if not goal_node:
            return jsonify({
                "status": "error",
                "message": "CRASH: Could not locate the movement goal in the tree"
            }), 400
        new_root = internal_merge(root = root_node, goal = goal_node)
        return jsonify({
            "status": "success",
            "message": f"MOVE SUCCESS: Formed [{new_root.label} {goal_node.label} {root_node.label}]",
            "parent_label": new_root.label
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"CRASH: {str(e)}"
        }), 400


        
if __name__ == '__main__':
    app.run(debug = True, port = 5000)