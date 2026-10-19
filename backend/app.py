from tree import Node
from lexicon import Feature
from operations import merge, agree, internal_merge
from validator import validate_derivation

from flask import Flask, jsonify, request
from flask_cors import CORS
import re

app = Flask(__name__)                                                   # Initializing the application
CORS(app)                                                               # Allow Cross-Origin Resource Sharing

@app.route('/api/status', methods = ['GET'])                            # Assuring connection (decorated with GET url)
def check_status():
    return jsonify({
        "status": "online",
        "message": "The Minimalist Validator API is working perfectly"
    })

# Turning the raw feature string into a Feature object
def parse_feature(raw_feat: str) -> Feature:
    raw = raw_feat.strip()
    if raw.startswith("uφ:") or raw.startswith("uphi:"):                                             # An uninterpretable feature (e.g., uD or uV)
        val = raw.split(":")[1]
        feat = Feature(type="phi", val=val, interpretable=False)
        feat.checked = True
        return feat
    if raw == "uφ" or raw == "uphi":
        return Feature(type="phi", val=None, interpretable=False)
    if raw.startswith("u"):
        return Feature(type="select", val=raw[1:], interpretable=False)
    return Feature(type="phi", val=raw, interpretable=True)

def find_target(node: Node):
    if getattr(node, 'is_target', False):
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
    


def build_tree_from_json(node_dict: dict) -> Node:
    if node_dict.get('type') == 'terminal':
        node = parse_node(node_dict['text'])
        
    if node_dict.get('type') == 'non-terminal':
        left_child = build_tree_from_json(node_dict['left'])
        right_child = build_tree_from_json(node_dict['right'])
        expected_label = node_dict.get('label', '')
        
        # 1. Identify Internal Merge (Movement)
        # Movement doesn't check selection features in this model; it just projects the target's exact label (e.g., TP -> TP).
        if expected_label == right_child.label:
            node = Node(
                features=right_child.features,
                left=left_child,
                right=right_child,
                label=expected_label
            )
            left_child.parent = node
            right_child.parent = node
        else:
            # 2. External Merge (Strict Directionality)
            # Compare the base label (stripping 'P') to figure out which child is the theoretical head
            base_expected = expected_label.replace('P', '')
            base_left = left_child.label.replace('P', '')
            
            if base_expected == base_left:
                node = merge(head=left_child, complement=right_child)
            else:
                node = merge(head=right_child, complement=left_child)
                # Preserve standard tree geometry (Specifier on left, Head on right)
                node.left = left_child
                node.right = right_child
                
        # Handle structural traces using our new boolean property
        if node_dict.get('isTrace', False):
            node.is_trace = True
            node.features = [f for f in node.features if f.type == "category"]
            
    node.is_target = node_dict.get('selected', False)
    return node


@app.route('/api/validate', methods = ['POST'])                         # Getting data from frontend (decorated with POST url)
def validate_workspace():
    # Receiving the data and extracting the items for the canvas
    payload = request.get_json()
    tree_data = payload.get('tree')

    if not tree_data:
        return jsonify({
            "status": "error",
            "message": "CRASH: the derivation board is empty"
        }), 400
    try:
        derived_root = build_tree_from_json(tree_data)
        converges = validate_derivation(derived_root)

        if converges:
            message = "SUCCESS: The derivation converges at Logical Form. All uninterpretable features are checked."
        else:
            message = "FAILURE: The derivation crashed at LF. Uninterpretable features survived."

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
    if "_t" in item_text:
        base_label = item_text.split('_')[0].strip()
        cat_val = base_label[:-1] if (base_label.endswith('P') and len(base_label) > 1) else base_label
        cat_feat = Feature(type="category", val=cat_val, interpretable=True)
        return Node(features=[cat_feat], label = item_text.strip())

    match = re.match(r"^([a-zA-Z]+)\s*\[(.*)\]$", item_text.strip())
    if not match:
        raise ValueError(f"Lexical analysis failed, '{item_text}' is malformed")
    
    label = match.group(1)
    raw_feats = [f.strip() for f in match.group(2).split(',') if f.strip()]
    node_features = [parse_feature(f) for f in raw_feats]
    cat_val = label[:-1] if (label.endswith('P') and len(label) > 1) else label                 # Turning phrases (ending with P) back to their heads (excluding P itself)
    node_features.insert(0, Feature(type =  "category", val = cat_val, interpretable = True))   # Creating the category feature (from the label outside the [])

    return Node(features = node_features, label = label)
    
@app.route('/api/merge', methods = ['POST'])
def execute_merge():
    payload = request.get_json()
    items = payload.get('items', [])

    if len(items) != 2:
        return jsonify({
            "status": "error",
            "messgage": "CRASH: merge requires exactly two items"
        }), 400

    try:
        item1 = build_tree_from_json(items[0])
        item2 = build_tree_from_json(items[1])

        try:
            merged_node = merge(head = item1, complement = item2)
        except ValueError:
            merged_node = merge(head = item2, complement = item1)

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

@app.route('/api/agree', methods=['POST'])
def execute_agree():
    payload = request.get_json()
    tree_data = payload.get('tree')

    if not tree_data:
        return jsonify({
            "status": "error",
            "message": "CRASH: No tree provided for Agree operation"
        }), 400

    try:
        selected_node = build_tree_from_json(tree_data)
        probe_node = selected_node.left if not selected_node.is_terminal() else selected_node
        goals_found = agree(probe = probe_node)

        feat_strings = []
        for f in probe_node.features:
            if f.type == "category":
                continue
            if f.type == "phi" and not f.interpretable:
                feat_strings.append(f"uφ:{f.val}" if f.val else "uφ")
            elif not f.interpretable:
                feat_strings.append(f"u{f.val}")
            else:
                feat_strings.append(f.val)
        updated_text = f"{probe_node.label} [{', '.join(feat_strings)}]"
        return jsonify({
            "status": "success",
            "message": f"AGREE SUCESS: Probe '{probe_node.label}' successfully checked its features",
            "updated_text": updated_text,
            "goals": goals_found
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"CRASH: {str(e)}"
        }), 400


@app.route('/api/move', methods=['POST'])
def execute_move():
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