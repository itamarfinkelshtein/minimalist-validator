from tree import Node

def validate_derivation(root: Node) -> tuple[bool, str]:
    """
    Validate the derivation of the syntax tree, checking that all uninterpretable features are checked.

    Args:
        root (Node): The root of the syntax tree to be validated.
    
    Returns:
        tuple[bool, str]: A tuple containing:
            bool: True if the derivation converged at LF, False otherwise.
            str: A pipe-separated string of crash messages detailing any surviving uninterpretable features, or an empty string if the derivation converges.
    """
    all_nodes = root.get_descendants()
    crash_messages = []
    
    for node in all_nodes:
        active_features = [f for f in node.features if f.is_active()]
        if active_features: # Failure to converge: a node left some feature active.
            for feat in active_features:
                feat_name = feat.val if feat.val else feat.type
                crash_messages.append(f"[{node.label}] left [u{feat_name}] unchecked")
                
    if crash_messages:
        return False, " | ".join(crash_messages)

    # Fallback option: The derivation converged and no crash messages appeared.    
    return True, ""