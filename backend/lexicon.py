class Feature:
    def __init__(self, type: str, val: str = None, interpretable: bool = True):
        self.type = type                        # The type of the feature (e.g., 'category', 'phi', 'case')
        self.val = val                          # The value of the feature (e.g., 'V', '3sg', 'nom')
        self.interpretable = interpretable      # Whether the feature is iF (true) or uF (false)
        self.checked = False                    # All features start unchecked by default

    def is_active(self):                        # A feature is active if it's uF and not checked
        return not self.interpretable and not self.checked

class LexicalItem:
    def __init__(self, phonology: str, features: list):
        self.phonology = phonology              # The phonological manifestaion of the item
        self.features = features                # A list of the item's features

    def get_active_features(self):              #returns a list of all active features of the item
        return [f for f in self.features if f.is_active()]

if __name__ == "__main__":
    feat_v = Feature(type = "category", val = "V", interpretable= True)
    feat_un = Feature(type = "select", val = "N", interpretable= False)

    verb = LexicalItem(phonology= "eat", features= [feat_v, feat_un])
    
    active = verb.get_active_features()
    print(f"The word {verb.phonology} has {len(active)} active features.")

    for feat in active:
        print(f" - Needs to check: [u{feat.val}]")