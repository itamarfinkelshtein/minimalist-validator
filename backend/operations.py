import copy
from tree import Node
from lexicon import Feature, is_phrase

def merge(head: Node, complement: Node) -> Node:
    """
    Merging a head X and its complement Y into an XP phrase, checking the head's selectional feature.

    Args:
        head (Node): the head (left node) of the new phrase.
        complement (Node): the complement (right node) of the new phrase.

    Returns:
        Node: the XP phrase node, whose children are the head and the complement.

    Raises:
        ValueError: If there is no match between the head's active selection features and the complement's category features.
    """
    
    # Fetching the head's active selction features and the complement's category feature, and ensuring their existance.
    select_features = [f for f in head.features if f.type == "select" and f.is_active()]
    cat_features = [f for f in complement.features if f.type == "category"]
    if not select_features:
        raise ValueError(f"MERGE CRASH: '{head.label}' has no active selection features")
    if not cat_features:
        raise ValueError(f"MERGE CRASH: '{complement.label}' has no categorical feature")

    head_req = select_features[0]
    comp_cat = cat_features[0]

    # Checking selection match, and performing the merge (checking and deleting).
    if head_req.val == comp_cat.val:
        head_req.checked = True
        print(f"MERGE SUCCESS: '{head.label}' checked [u{head_req.val}] against '{complement.label}'")
    else:
        raise ValueError(f"MERGE CRASH: '{head.label}' requires [u{head_req.val}], but got '{comp_cat.val}'")

    # Collecting the projected features for the parent XP node (from the head, with phi-feature and case from the complement in case of DP creation).
    projected_features = list(head.features)
    if head.label == "D" and complement.label == "N": #This is a DP
        noun_phis =  [f for f in complement.features if f.type == "phi" and f.interpretable]
        noun_case = [f for f in complement.features if f.type == "case"]
        projected_features.extend(noun_phis)
        projected_features.extend(noun_case)

    # Creating the parent node and setting the head and the complement's parent to it.
    projected_label = head.label if is_phrase(head.label) else head.label + "P"
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
    """
    Adjoins two phrases where one is an adjunct of the other, not checking any feature.
    
    Args:
        target (Node): The node whose features will be projected to the parent phrase node.
        left_node (Node): The left node of the operation.
        right_node (Node): The right node of the operation.
    
    Returns:
        Node: The resulting parent node, whose features are inherited from the target node.

    Raises:
        ValueError: If one of the nodes does not represent a phrase.
    """

    if not (is_phrase(left_node.label) and is_phrase(right_node.label)):
        raise ValueError(f"ADJOIN CRASH: both nodes should be phrase nodes.")
    
    projected_features = list(target.features)  # Using a shallow copy so feature checkings will affect both the parent and the head nodes.
    
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
    """
    Executing the agree operation for the probe node, checkin uninterpretable phi-features and assigning case.

    Traversing the C-command domain to find interpretable phi-features for the probe's active uninterpretable phi-features,
    and simultaneously assigning case to the goal, based on the probe's category type.

    Args:
        probe (Node): The node searching an item with uninterpretable phi-features to valuate.
    
    Returns:
        list[str]: A list of the labels of the goals that were successfully found and valued.

    Raises:
        ValueError: If a Relativized Minimality violation occurs (a defective intervener 
            is encountered that matches the feature type but cannot value the probe).
        ValueError: If the probe possesses an active, uninterpretable phi-feature but 
            no valid goal can be found in its entire c-command domain.
    """
    # Collecting the active (uninterpretable and not yet checked) phi-features of the probe.
    active_features = [f for f in probe.features if f.is_active() and f.type == "phi"]
    
    # Safely determine the inherent Case this probe assigns
    clean_label = probe.label.split('_')[0]
    base_label = clean_label[:-1] if is_phrase(clean_label) else clean_label
    
    assignable_case = None
    if base_label == "T":
        assignable_case = "nom"
    elif base_label == "v":
        assignable_case = "acc"
    elif base_label == "P":
        assignable_case = "obl"  # Covers oblique and dative complements
    elif base_label == "D":
        assignable_case = "gen"  # For possessive DPs
        
    if not active_features and not assignable_case: # The probe does not need any phi-features and cannot assign case.
        return []

    # Looking for a goal to agree with.    
    domain = probe.get_c_command_domain()
    goals_found = []
    
    # 1. Standard Phi-Feature Agreement (T and v)
    for req_feat in active_features:
        goal_found = False
        for potential_goal in domain: # Important: The order of probing is Pre-Order to reflect the true order of probing in minimalist theory.
            matching_type_features = [f for f in potential_goal.features if f.type == req_feat.type] # Checking if the potential goal's phi-feature match the features the probe needs.
            
            if matching_type_features:
                valid_goals = [f for f in matching_type_features if f.interpretable] # Checking that the matched feature is also interpretable (and therefore is a phi-feature)
                
                if valid_goals:
                    # Success: Value the Probe
                    if req_feat.val == None:
                        req_feat.val = valid_goals[0].val
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
                    break # Continue looking for a match for the next requested feature.
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
    """
    Creating a copy of the node in goal position, merging it with the root node in SPEC position, and turning the original node to a trace.

    Parameters:
        root (Node): The node (in complement position) to be merged with the moved item.
        goal (Node): The node to be copied to SPEC position and turn to a trace.
    
    Returns:
        Node: The parent phrase node, whose children are the copy of the goal and the root.
    """
    moved_item = copy.deepcopy(goal)    # Making a deep copy of the goal to merge with the root.
    
    # Turning the original goal to a trace
    goal.label = goal.label + "_t"
    goal.features = []
    goal.is_trace = True

    # Merging the moved item (in SPEC position) and the root (in complement position) and establishing parent pointers.
    parent_node = Node(
        features = root.features,
        left = moved_item,
        right = root,
        label = root.label
    )
    moved_item.parent = parent_node
    root.parent = parent_node

    return parent_node