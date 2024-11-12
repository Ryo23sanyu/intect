def format_damages(damages):
    formatted_damages = ",".join(list(dict.fromkeys(damages)))
    return formatted_damages

def process_damage(damage, index):
    parts = damage.split(',')
    if index == 0 and len(parts) > 1:
        first_damage = parts[0].split(':')[0]
        after_damage = ':' + parts[1].strip()
        return first_damage + after_damage
    return damage

def process_related_damages(damages):
    processed_related_damages = []
    for damage in damages:
        colon_index = damage.find(":")
        if colon_index != -1:
            before_colon = damage[:colon_index].strip()
            after_colon = damage[colon_index + 1:].strip()
            if before_colon and after_colon:
                processed_related_damages.append(f"{before_colon}:{after_colon}")
    return processed_related_damages