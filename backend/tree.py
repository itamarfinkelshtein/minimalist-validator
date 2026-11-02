from lexicon import Feature

class Node:
    """
    A node in the syntactic tree.
    Terminal nodes ('leaves') represent lexical items, Internal nodes represent phrases.

    Attributes:
        features (list[feature]): A list of the features in the node.
        left (Node): Pointer to the left child
        right (Node): Pointer to the right child
        label (str): The node's label (e.g., 'VP', 'N'). This is not to be confused with the text/phonology of terminal nodes.
        parent (Node): Pointer to the parent of the node.
        is_trace (bool): Whether the node is part of a trace of movement.
        node_id (int): A numeral id for necessary operations.
    """
    def __init__(self, features: list[Feature], left = None, right = None, label: str = "", parent = None, node_id = None):
        self.features = features
        self.left = left
        self.right = right
        self.label = label
        self.parent = parent
        self.is_trace = False                   # All nodes are in their base position by default.
        self.node_id = node_id

    def is_terminal(self) -> bool:
        """
        Checking if the node has no children.
        
        Returns:
            bool: True is the node is terminal, False otherwise.
        """
        return self.left is None and self.right is None

    def get_leaves(self) -> list[Node]:
        """
        Recursively collect all leaves in the node's domain.
        
        Returns:
            list[Node]: a list of the leaves in the node's domain, from left to right.
        """
        if self.is_terminal():
            return [self]
        
        leaves = []
        if self.left:
            leaves.extend(self.left.get_leaves())
        if self.right:
            leaves.extend(self.right.get_leaves())
        return leaves

    def get_descendants(self) -> list[Node]:
        """
        Recursively return the entire domain of the node.

        Returns:
            list[Node]: a list of the node's domain (including itself), in Pre-Order.
        """
        desc = [self]
        if self.left:
            desc.extend(self.left.get_descendants())
        if self.right:
            desc.extend(self.right.get_descendants())
        return desc


    def get_c_command_domain(self) -> list[Node]:
        """
        Collect the C-command domain of the node.

        Returns:
            list[Node]: a list of the node's C-command domain, in Pre-Order.
        """
        # Node A C-commands node B iff:
        #   1. A does not dominate B.
        #   2. B does not dominate A.
        #   3. The first node that dominates A also dominates B.
        # In other words, the C-command domain of A is its sister's entire domain.
        
        if self.parent == None:                 # Identify the sibling node (if exists) safely.
            return []
        
        if self.parent.left == self:
            sibling = self.parent.right
        else:
            sibling = self.parent.left
        if sibling == None:                     
            return []

        return sibling.get_descendants()