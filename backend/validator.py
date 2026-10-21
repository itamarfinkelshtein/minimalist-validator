from tree import Node

def validate_derivation(root: Node) -> tuple[bool, str]:
    all_nodes = root.get_descendants()
    crash_messages = []
    
    for node in all_nodes:
        active_features = [f for f in node.features if f.is_active()]
        if active_features:
            for feat in active_features:
                feat_name = feat.val if feat.val else feat.type
                crash_messages.append(f"[{node.label}] left [u{feat_name}] unchecked")
                
    if crash_messages:
        return False, " | ".join(crash_messages)
        
    return True, ""


if __name__ == "__main__":
    from backend.lexicon import Feature
    from backend.operations import merge
    
    # 1. Build a Verb and a Noun
    v_node = Node(features=[Feature("category", "V"), Feature("select", "N", False)], label="V")
    n_node = Node(features=[Feature("category", "N"), Feature("phi", "3sg")], label="N")
    vp_node = merge(v_node, n_node)
    
    # 2. Build Tense with a [uphi] feature that NEVER gets checked
    t_node = Node(features=[Feature("category", "T"), Feature("select", "V", False), Feature("phi", None, False)], label="T")
    tp_node = merge(t_node, vp_node)
    
    # Note: We are purposely NOT calling agree(t_node) here.
    
    # 3. Run the Validator
    print("\n--- Running LF Validation ---")
    validate_derivation(tp_node)