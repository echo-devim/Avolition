# Frequency can have a value between 1 and 10
# A lower value means that the item has less chances to be selected by RandomObject class
# Availability is the number of items in the shop for the current session, when the game is restarted the available items
# return to their original value defined in the following list
items = [
        {"name" : "health flask", "price" : 4, "count" : 0, "available" : 3, "description": "Potion to restore your health +20", "icon" : "icon/icon_flask.png", "frequency" : 10},
        {"name" : "armor flask", "price" : 5, "count" : 0, "available" : 1, "description": "Potion to increase your armor +1", "icon" : "icon/armor_flask.png", "frequency" : 9},
        {"name" : "attack boost", "price" : 7, "count" : 0, "available" : 2, "description": "Increase your attack power +0.5", "icon" : "icon/items_free_l/64x64/sword_blue.png", "frequency" : 5},
        {"name" : "health boost", "price" : 8, "count" : 0, "available" : 1, "description": "Slowly restore your health for 30 seconds", "icon" : "icon/items_free_l/64x64/gem.png", "frequency" : 4},
        {"name" : "torch", "price" : 4, "count" : 0, "available" : 1, "description": "Increase your light radius", "icon" : "icon/items_free_l/64x64/torch.png", "frequency" : 5},
        {"name" : "boots", "price" : 5, "count" : 0, "available" : 2, "description": "Increase your speed +0.1", "icon" : "icon/items_free_l/64x64/boots.png", "frequency" : 6},
        {"name" : "critical damage", "price" : 9, "count" : 0, "available" : 1, "description": "Increase the chance to inflict critical damage", "icon" : "icon/items_free_l/64x64/sword_power.png", "frequency" : 3},
        {"name" : "invincible ring", "price" : 12, "count" : 0, "available" : 1, "description": "You will not receive any damage for 10 seconds", "icon" : "icon/items_free_l/64x64/ring2.png", "frequency" : 2},
        {"name" : "items boost", "price" : 10, "count" : 0, "available" : 2, "description": "You will find items more often", "icon" : "icon/items_free_l/64x64/bag.png", "frequency" : 1},
        {"name" : "great attack boost", "price" : 12, "count" : 0, "available" : 1, "description": "Increase your attack power +2", "icon" : "icon/items_free_l/64x64/sword_yellow.png", "frequency" : 1.5},
]

def getItemIndex(item_name):
    for i in range(0,len(items)):
        if items[i]['name'] == item_name:
            return i
    return None
