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
        noun_case = [f for f in complement.features if f.type == "case"]
        projected_features.extend(noun_phis)
        projected_features.extend(noun_case)

    # Creating the parent node
    projected_label = head.label if (head.label.endswith('P') and len(head.label) > 1) else head.label + "P"
    parent_node = Node(
        features = projected_features,
        left = head,
        right = complement,
        label = projected_label
        )
    head.parent = parent_node
    complement.parent = parent_node
    return parent_node

def adjoin(target: Node, left_node: Node, right_node: Node) -> Node:
    # Use a shallow copy! Create a new list, but keep references to the exact same Feature objects.
    # If a feature gets checked on this higher segment, it updates the original head simultaneously.
    projected_features = list(target.features)
    
    parent_node = Node(
        features = projected_features,
        left = left_node,
        right = right_node,
        label = target.label
    )
    
    left_node.parent = parent_node
    right_node.parent = parent_node
    return parent_node

def agree(probe: Node):
    # AGREE RESTRICTION: Only uninterpretable phi-features trigger long-distance Agree. 
    # Selection features (like uD) are strictly for Merge.
    active_features = [f for f in probe.features if f.is_active() and f.type == "phi"]
    
    # Safely determine the inherent Case this probe assigns
    clean_label = probe.label.split('_')[0]
    base_label = clean_label[:-1] if (clean_label.endswith('P') and len(clean_label) > 1) else clean_label
    
    assignable_case = None
    if base_label == "T":
        assignable_case = "nom"
    elif base_label == "v":
        assignable_case = "acc"
    elif base_label == "P":
        assignable_case = "obl"  # Covers oblique and dative complements
    elif base_label == "D":
        assignable_case = "gen"  # Future-proofing for possessive DPs
        
    if not active_features and not assignable_case:
        return []
        
    domain = probe.get_c_command_domain()
    goals_found = []
    
    # 1. Standard Phi-Feature Agreement (T and v)
    for req_feat in active_features:
        goal_found = False
        for potential_goal in domain:
            matching_type_features = [f for f in potential_goal.features if f.type == req_feat.type]
            
            if matching_type_features:
                valid_goals = [f for f in matching_type_features if f.interpretable]
                
                if valid_goals:
                    # Success: Value the Probe
                    goal_feat = valid_goals[0]
                    if req_feat.val == None:
                        req_feat.val = goal_feat.val
                    req_feat.checked = True
                    print(f"AGREE SUCCESS: '{probe.label}' checked and valued [u{req_feat.type}:{req_feat.val}] against '{potential_goal.label}'")
                    goals_found.append(potential_goal.label)
                    goal_found = True
                    
                    # CASE REFLEX: Automatically value Case on the goal (and its percolated children)
                    if assignable_case:
                        for gf in potential_goal.features:
                            if gf.type == "case" and not gf.checked:
                                gf.val = assignable_case
                                gf.checked = True
                                print(f"CASE SUCCESS: '{probe.label}' assigned [{assignable_case}] case to '{potential_goal.label}'")
                        assignable_case = None # Discharge the case so it isn't assigned twice
                    break
                else:
                    raise ValueError(f"AGREE CRASH: Relativized Minimality violation. '{potential_goal.label}' intervenes but cannot value the Probe.")
                    
        if not goal_found:
            raise ValueError(f"AGREE CRASH: '{probe.label}' found no valid goal for [u{req_feat.val}] in its domain")
            
    # 2. Standalone Case Assignment (for P, which assigns case but lacks phi-probes)
    if assignable_case:
        for potential_goal in domain:
            unvalued_case_feats = [f for f in potential_goal.features if f.type == "case" and not f.checked]
            if unvalued_case_feats:
                for gf in unvalued_case_feats:
                    gf.val = assignable_case
                    gf.checked = True
                goals_found.append(potential_goal.label)
                print(f"CASE SUCCESS: '{probe.label}' assigned [{assignable_case}] case to '{potential_goal.label}'")
                assignable_case = None
                break
                
    return goals_found
    
def internal_merge(root: Node, goal: Node) -> Node:
    moved_item = copy.deepcopy(goal)                                                        # Making a deep copy of the goal to merge with the root
    
    goal.label = goal.label + "_t"                                                          # The original goal turns into a trace
    goal.features = []
    goal.is_trace = True

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