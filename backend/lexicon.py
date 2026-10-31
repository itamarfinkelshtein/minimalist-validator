def is_phrase(label: str) -> bool:
    """
    Checking if a label represents a phrase (e.g., 'NP', 'VP', 'DP', 'PP', 'vP' etc.)

    Args:
        label (str): The label to be checked.
    
    Returns:
        bool: True if the label represents a phrase, False otherwise.
    """
    return label.endswith('P') and len(label) > 1

class Feature:
    """
    A certain linguistic feature of a lexical item.

    Attributes:
        type (str): The type of the feature (e.g., 'category', 'phi', 'case').
        val (str): The value of the feature (e.g., 'V', '3sg', 'nom').
        interpretable (bool): Whether the feature is iF (true) or uF (false).
        checked (bool): Whether the feature is currently checked.
    """
    def __init__(self, type: str, val: str = None, interpretable: bool = True):
        self.type = type
        self.val = val
        self.interpretable = interpretable
        self.checked = False                    # All features start unchecked by default

    def is_active(self) -> bool:
        """
        Checks if the feature is active (meaning that it's uninterpretable and not checked).

        Returns:
            bool: True if the feature is currently active, False otherwise.
        """
        return not self.interpretable and not self.checked