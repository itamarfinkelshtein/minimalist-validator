from lexicon import Feature, LexicalItem

class Node:
    def __init__(self, features: list, left = None, right = None, label: str = "", parent = None):
        self.features = features                # A list of the features in the node
        self.left = left                        # Pointer to the left child
        self.right = right                      # Pointer to the right child
        self.label = label
        self.parent = parent                      # The node's label (e.g., 'VP', 'N')
        self.is_trace = False

    def is_terminal(self):                      # Checking if the node hasn't any children
        return self.left is None and self.right is None

    def get_leaves(self):                       # Recursively collect all leaves under the node
        if self.is_terminal():
            return [self]
        
        leaves = []
        if self.left:
            leaves.extend(self.left.get_leaves())
        if self.right:
            leaves.extend(self.right.get_leaves())
        return leaves

    def get_descendants(self) -> list:          # Recursively return the entire domain of the node in Pre-Order
        desc = [self]
        if self.left:
            desc.extend(self.left.get_descendants())
        if self.right:
            desc.extend(self.right.get_descendants())
        return desc


    def get_c_command_domain(self, original_caller = None) -> list:
        # Node A C-commands node B iff:
        #   1. A does not dominate B.
        #   2. B does not dominate A.
        #   3. The first node that dominates A also dominates B.
        
        if self.parent == None:                 # Identify the sibling node (if exists)
            return []
        if self.parent.left == self:
            sibling = self.parent.right
        else:
            sibling = self.parent.left

        if sibling == None:                     
            return []

        return sibling.get_descendants()        # Return the sibling's domain as the C-command domain of the node


if __name__ == "__main__":
    from backend.lexicon import Feature # Ensure Feature is imported for testing

    # 1. Build a mock tree structure: [VP V [DP D N]]
    v_node = Node(features=[], label="V")
    d_node = Node(features=[], label="D")
    n_node = Node(features=[], label="N")
    
    # 2. Merge D and N into a DP
    dp_node = Node(features=[], left=d_node, right=n_node, label="DP")
    d_node.parent = dp_node
    n_node.parent = dp_node
    
    # 3. Merge V and DP into a VP
    vp_node = Node(features=[], left=v_node, right=dp_node, label="VP")
    v_node.parent = vp_node
    dp_node.parent = vp_node

    # 4. Test the c-command domain of the head verb
    domain = v_node.get_c_command_domain()
    
    print(f"The c-command domain of '{v_node.label}' contains {len(domain)} nodes:")
    for node in domain:
        print(f" - {node.label}")