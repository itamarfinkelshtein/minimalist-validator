from tree import Node

def validate_derivation(root: Node) -> bool:
    all_nodes = root.get_descendants()                                          # Getting all nodes in the tree
    derivation_converges = True

    for node in all_nodes:
        active_featues = [f for f in node.features if f.is_active()]            # Checking if there are any unchecked features
        if active_featues:
            derivation_converges = False
            for feat in active_featues:
                print(f"CRASH AT LF: '{node.label}' still has unchecked [u{feat.type}] feature")
    
    if derivation_converges:
        print("\nSUCCESS: The derivation converges at Logical Form. All uninterpretable features are checked")
    else:
        print("\nFAILURE: The derivation crashed. Uninterpretable features survived to the interface")
        
    return derivation_converges


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