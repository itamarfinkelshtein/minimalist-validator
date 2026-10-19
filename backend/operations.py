import copy
from tree import Node
from lexicon import Feature, LexicalItem

def merge(head: Node, complement: Node) -> Node:
    select_features = [f for f in head.features if f.type == "select" and f.is_active()]    # The categorical feature the head selects
    cat_features = [f for f in complement.features if f.type == "category"]                 # The categorical feature of the complement

    # Ensuring existence of selected feature of the head and categorical feature of the complement
    if not select_features:
        raise ValueError(f"MERGE CRASH: '{head.label}' has no active selection features")
    if not cat_features:
        raise ValueError(f"MERGE CRASH: '{complement.label}' has no categorical feature")
    head_req = select_features[0]
    comp_cat = cat_features[0]

    if head_req.val == comp_cat.val:
        head_req.checked = True                                                             # Checking and deleting the feature
        print(f"MERGE SUCCESS: '{head.label}' checked [u{head_req.val}] against '{complement.label}'")
    else:
        raise ValueError(f"MERGE CRASH: '{head.label}' requires [u{head_req.val}], but got '{comp_cat.val}'")

    projected_features = list(head.features)
    if head.label == "D" and complement.label == "N":
        noun_phis =  [f for f in complement.features if f.type == "phi" and f.interpretable]
        projected_features.extend(noun_phis)

    # Creating the parent node
    projected_label = head.label if head.label.endswith('P') else head.label + "P"
    parent_node = Node(
        features = projected_features,
        left = head,
        right = complement,
        label = projected_label
        )
    head.parent = parent_node
    complement.parent = parent_node
    return parent_node

def agree(probe: Node):
    active_features = [f for f in probe.features if f.is_active()]                          # Finding the features which still need to be checked
    if not active_features:                                                                 # (if any)
        return []

    domain = probe.get_c_command_domain()
    goals_found = []

    for req_feat in active_features:                                                        # Going over all requested features of the node
        goal_found = False
        for potential_goal in domain:                                                       # Going over all potential nodes in the C-domain
            matching_features = [f for f in potential_goal.features 
                                if f.type == req_feat.type                                  # A matching feature matches the requested in type
                                and f.interpretable]                                        # and is interpretable
            if matching_features:
                goal_feat = matching_features[0]                                            # Should be only one
                
                if req_feat.val == None:
                    req_feat.val = goal_feat.val                                            # Copying the value of the found node into the probe node
                req_feat.checked = True                                                     # Checking the uninterpretable requested feature
                print(f"AGREE SUCCESS: '{probe.label}' checked and valued [u{req_feat.type}:{req_feat.val}] against '{potential_goal.label}'")
                goals_found.append(potential_goal.label)
                goal_found = True
                break

        if not goal_found:
            raise ValueError(f"AGREE CRASH: '{probe.label}' found no valid goal for [u{req_feat.val}] in its domain")
    return goals_found
    
def internal_merge(root: Node, goal: Node) -> Node:
    moved_item = copy.deepcopy(goal)                                                        # Making a deep copy of the goal to merge with the root
    
    goal.label = goal.label + "_t"                                                          # The original goal turns into a trace
    goal.features = []

    parent_node = Node(                                                                     # Merging the root and the moved item (in SPEC position)
        features = root.features,
        left = moved_item,
        right = root,
        label = root.label
    )
    moved_item.parent = parent_node                                                         # Establishing parent pointers
    root.parent = parent_node

    return parent_node
  
if __name__ == "__main__":
    from backend.tree import Node
    from backend.lexicon import Feature
    
    # 1. Build the DP (The Goal to be moved)
    dp_cat = Feature(type="category", val="D", interpretable=True)
    dp_node = Node(features=[dp_cat], label="DP")
    
    # 2. Build the V and External Merge with DP
    v_cat = Feature(type="category", val="V", interpretable=True)
    v_select = Feature(type="select", val="D", interpretable=False)
    v_node = Node(features=[v_cat, v_select], label="V")
    vp_node = merge(head=v_node, complement=dp_node)
    
    # 3. Build T and External Merge with VP
    t_cat = Feature(type="category", val="T", interpretable=True)
    t_select = Feature(type="select", val="V", interpretable=False)
    t_node = Node(features=[t_cat, t_select], label="T")
    tp_node = merge(head=t_node, complement=vp_node)
    
    # 4. Trigger Internal Merge (Move)
    print("\n--- Triggering Internal Merge (Move) ---")
    final_tree = internal_merge(root=tp_node, goal=dp_node)
    
    # 5. Verify the Structure
    print(f"The new root is: {final_tree.label}")
    print(f"The Specifier (left child) is: {final_tree.left.label}")
    
    # Let's extract all the terminal leaves to see if the trace was left behind!
    leaves = final_tree.get_leaves()
    print(f"Leaves in the final tree (left-to-right): {[leaf.label for leaf in leaves]}")