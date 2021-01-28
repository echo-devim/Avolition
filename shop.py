# Frequency can have a value between 1 and 10
# A lower value means that the item has less chances to be selected by RandomObject class
items = [
        {"name" : "health flask", "price" : 5, "count" : 0, "available" : 10, "description": "Potion to restore your health", "icon" : "icon/icon_flask.png", "frequency" : 10},
        {"name" : "armor flask", "price" : 3, "count" : 0, "available" : 10, "description": "Potion to increase your armor +1", "icon" : "icon/armor_flask.png", "frequency" : 9},
        {"name" : "attack boost", "price" : 8, "count" : 0, "available" : 5, "description": "Increase your attack power +1", "icon" : "icon/items_free_l/64x64/sword_power.png", "frequency" : 5},
        {"name" : "defence boost", "price" : 12, "count" : 0, "available" : 1, "description": "Increase your armor +3", "icon" : "icon/items_free_l/64x64/shield.png", "frequency" : 4},
        {"name" : "torch", "price" : 10, "count" : 0, "available" : 1, "description": "Increase your light radius", "icon" : "icon/items_free_l/64x64/torch.png", "frequency" : 5},
        {"name" : "boots", "price" : 8, "count" : 0, "available" : 1, "description": "Increase your speed +0.5", "icon" : "icon/items_free_l/64x64/boots.png", "frequency" : 6},
        {"name" : "invisible ring", "price" : 15, "count" : 0, "available" : 5, "description": "You will be invisible to monsters for 15 seconds", "icon" : "icon/items_free_l/64x64/ring1.png", "frequency" : 3},
        {"name" : "invincible ring", "price" : 18, "count" : 0, "available" : 3, "description": "You will not receive any damage for 20 seconds", "icon" : "icon/items_free_l/64x64/ring2.png", "frequency" : 2},
        {"name" : "great defence boost", "price" : 18, "count" : 0, "available" : 1, "description": "Increase your armor +5", "icon" : "icon/items_free_l/64x64/shield2.png", "frequency" : 1},
        {"name" : "great attack boost", "price" : 16, "count" : 0, "available" : 2, "description": "Increase your attack power +3", "icon" : "icon/items_free_l/64x64/sword_blue.png", "frequency" : 1.5},
]

def getItemIndex(item_name):
    for i in range(0,len(items)):
        if items[i]['name'] == item_name:
            return i
    return None