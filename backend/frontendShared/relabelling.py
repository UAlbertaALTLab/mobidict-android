from backend.types import FSTTag
from backend.relabelling import read_labels


# Check here - how are the tags that are passed None?
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

    return {
        "english": labels.english,
        "linguistic": labels.linguistic_short,
        "source_language": labels.cree,
    }.get(label_setting, labels.english)



def relabel_source(pos: str):
    """
    Should take in a class and return the plain english labelling for it
    So if I pass in "VTA-1", I should get back:
    tâpiskôc: wîcihêw
    """
    return read_labels().cree.get(pos)
    
def relabel_plain_english(pos: str):
    """
    Should take in a class and return the plain english labelling for it
    So if I pass in "VTA-1", I should get back:
    like: wîcihêw
    """
    return read_labels().english.get(pos)

def relabel_linguistic_long(pos: str):
    """
    Should take in a class and return the plain english labelling for it
    So if I pass in "VTA-1", I should get back:
    transitive animate verb – class 1: regular
    """
    return read_labels().linguistic_long.get(pos)