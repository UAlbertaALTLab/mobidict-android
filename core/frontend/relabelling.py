from core.types import FSTTag
from core.relabelling import read_labels

def relabel(tags, labels="english"):
    # Default label = "english"
    label_setting = labels
    
    relabeller = label_setting_to_relabeller(label_setting)
    
    if label := relabeller.get_longest(tags):
        if label_setting == "source_language":
            # TODO: Finish implementing this.
            # return orth_tag(context, label)
            print("Label Setting: Source language")
        return label

    print("Could not find relabelling for tags: %r", tags)
    return "+".join(tags)
    

def label_setting_to_relabeller(label_setting: str):
    labels = read_labels()
    
    # TODO: Solve the source_language

    return {
        "english": labels.english,
        "linguistic": labels.linguistic_short,
        # "source_language": labels.source_language,
    }.get(label_setting, labels.english)
    
    
    
    