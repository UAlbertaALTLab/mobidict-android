def cells_contains_only_column_labels(cells):
    label_amount = 0
    for cell in cells:
        if not cell['is_inflection'] and (cell['is_empty'] or cell['label_for'] == 'col'):
            if not cell['is_empty'] and cell['label_for'] == 'col':
                label_amount += 1
            continue
        else:
            return [False, 0]
    return [True, label_amount]


def is_core_column_header(cells):
    for cell in cells:
        if not cell['is_empty'] and cell['is_label'] and cell['label'][0] == "Core":
            return True
    return False