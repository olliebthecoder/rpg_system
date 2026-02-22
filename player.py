from character import Character


def create_ninja():
    # 100HP
    # 15 attack power
    # 75 speed
    # 45 attack speed
    # 15% defense
    # 60% crit chance

    return Character("ninja", 100, 15, 75, 45, 15, 60)


def create_orc():
    # 155HP
    # 20 attack power
    # 25 speed
    # 30 attack speed
    # 45% defense
    # 20% crit chance

    return Character("orc", 155, 20, 25, 30, 45, 20)


def choose_character():
    print("choose your character \n")
    print("1) Ninja")
    print("2) Orc")

    choice = input("> ")

    if choice == "1":
        return create_ninja()
    elif choice == "2":
        return create_orc()
    else:
        print("invalid choice. defaulting to Ninja")
        return create_ninja()
