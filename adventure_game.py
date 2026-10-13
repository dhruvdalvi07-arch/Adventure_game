#!/usr/bin/env python3
"""Advanced Extensible Text-Based Adventure Game Engine."""

from __future__ import annotations

import os
import secrets
import sys
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple


# =====================================================================
# Terminal Presentation Utilities
# =====================================================================

class UI:
    """Handles formatted terminal output with optional ANSI styling."""
    _USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    RESET = "\033[0m" if _USE_COLOR else ""
    BOLD = "\033[1m" if _USE_COLOR else ""
    DIM = "\033[2m" if _USE_COLOR else ""
    RED = "\033[91m" if _USE_COLOR else ""
    GREEN = "\033[92m" if _USE_COLOR else ""
    YELLOW = "\033[93m" if _USE_COLOR else ""
    CYAN = "\033[96m" if _USE_COLOR else ""
    MAGENTA = "\033[95m" if _USE_COLOR else ""

    @classmethod
    def wrap(cls, text: str, width: int = 76) -> str:
        return textwrap.fill(text, width=width)

    @classmethod
    def print_wrapped(cls, text: str, prefix: str = "") -> None:
        wrapped = textwrap.fill(text, width=76, initial_indent=prefix, subsequent_indent=prefix)
        print(wrapped)

    @classmethod
    def divider(cls) -> None:
        print(f"{cls.DIM}{'─' * 76}{cls.RESET}")


# =====================================================================
# Core Domain Models
# =====================================================================

class ItemType(Enum):
    GENERIC = "generic"
    WEAPON = "weapon"
    CONSUMABLE = "consumable"
    KEY = "key"


@dataclass
class Item:
    id: str
    name: str
    description: str
    item_type: ItemType = ItemType.GENERIC
    damage_bonus: int = 0
    heal_amount: int = 0
    use_effect: Optional[str] = None  # Identifier for special event triggers


@dataclass
class Entity:
    """Represents a combatant (Player or Monster)."""
    name: str
    hp: int
    max_hp: int
    base_damage: int
    is_alive: bool = True

    def take_damage(self, amount: int) -> int:
        actual_damage = min(self.hp, amount)
        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
        return actual_damage

    def heal(self, amount: int) -> int:
        recovered = min(self.max_hp - self.hp, amount)
        self.hp += recovered
        return recovered


@dataclass
class Enemy(Entity):
    description: str = ""
    xp_reward: int = 20
    loot: Optional[Item] = None


@dataclass
class Room:
    id: str
    title: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)       # direction -> room_id
    items: Dict[str, Item] = field(default_factory=dict)       # item_id -> Item
    enemy: Optional[Enemy] = None
    locked_exits: Dict[str, str] = field(default_factory=dict) # direction -> required_item_id
    visited: bool = False


# =====================================================================
# Player State & Inventory
# =====================================================================

class Player(Entity):
    def __init__(self, name: str = "Wanderer", hp: int = 40, base_damage: int = 6):
        super().__init__(name=name, hp=hp, max_hp=hp, base_damage=base_damage)
        self.inventory: Dict[str, Item] = {}
        self.equipped_weapon: Optional[Item] = None
        self.current_room_id: str = "cellar"

    @property
    def total_damage(self) -> int:
        bonus = self.equipped_weapon.damage_bonus if self.equipped_weapon else 0
        return self.base_damage + bonus


# =====================================================================
# Game World Builder
# =====================================================================

class WorldBuilder:
    @staticmethod
    def build_world() -> Dict[str, Room]:
        # Item Definitions
        rusty_dagger = Item(
            id="dagger",
            name="Rusty Dagger",
            description="A pitted iron dagger. Better than bare fists.",
            item_type=ItemType.WEAPON,
            damage_bonus=4,
        )
        brass_key = Item(
            id="brass_key",
            name="Brass Key",
            description="An ornate key etched with a stylized serpent.",
            item_type=ItemType.KEY,
        )
        health_potion = Item(
            id="potion",
            name="Health Potion",
            description="A vial of shimmering crimson liquid.",
            item_type=ItemType.CONSUMABLE,
            heal_amount=20,
        )
        sun_amulet = Item(
            id="amulet",
            name="Sun Amulet",
            description="An ancient golden talisman humming with warmth.",
            item_type=ItemType.GENERIC,
            use_effect="break_barrier",
        )

        # Enemies
        crypt_ghoul = Enemy(
            name="Crypt Ghoul",
            hp=18,
            max_hp=18,
            base_damage=5,
            description="A withered silhouette with sunken, ravenous eyes.",
            loot=brass_key,
        )
        dungeon_warden = Enemy(
            name="Gargoyle Warden",
            hp=35,
            max_hp=35,
            base_damage=8,
            description="A hulking stone monstrosity awakened from its pedestal.",
        )

        # Room Construction
        cellar = Room(
            id="cellar",
            title="Forgotten Cellar",
            description=(
                "Cold air drips through cracks in ancient cobblestone. "
                "Water seeps down moss-covered walls. To the north sits a heavy oak door."
            ),
            exits={"north": "antechamber"},
            items={"dagger": rusty_dagger},
        )

        antechamber = Room(
            id="antechamber",
            title="Shattered Antechamber",
            description=(
                "Rubble from a collapsed vaulted ceiling carpets the floor. "
                "Corridors stretch to the east and west. To the north stands a reinforced iron gate."
            ),
            exits={
                "south": "cellar",
                "east": "ossuary",
                "west": "alchemist_lab",
                "north": "sanctum",
            },
            locked_exits={"north": "brass_key"},
        )

        ossuary = Room(
            id="ossuary",
            title="Dusty Ossuary",
            description=(
                "Stacks of bone line every niche in the rock. The stench of decay "
                "hangs heavy in the stifling stillness."
            ),
            exits={"west": "antechamber"},
            enemy=crypt_ghoul,
        )

        alchemist_lab = Room(
            id="alchemist_lab",
            title="Ruined Laboratory",
            description=(
                "Shattered beakers and overturned alembics cover ruined worktables. "
                "A preserved leather pouch rests beside an extinguished brazier."
            ),
            exits={"east": "antechamber"},
            items={"potion": health_potion, "amulet": sun_amulet},
        )

        sanctum = Room(
            id="sanctum",
            title="Sanctum of the Sun",
            description=(
                "Pillars of white granite rise into moonlit rafters. "
                "In the center, a towering stone guardian blocks the grand archway to freedom."
            ),
            exits={"south": "antechamber"},
            enemy=dungeon_warden,
        )

        return {
            "cellar": cellar,
            "antechamber": antechamber,
            "ossuary": ossuary,
            "alchemist_lab": alchemist_lab,
            "sanctum": sanctum,
        }


# =====================================================================
# Game Engine & Controller
# =====================================================================

class GameEngine:
    def __init__(self) -> None:
        self.world: Dict[str, Room] = WorldBuilder.build_world()
        self.player: Player = Player()
        self.game_running: bool = True
        self.rng = secrets.SystemRandom()

        # Command Dispatch Table
        self.commands: Dict[str, Callable[[List[str]], None]] = {
            "go": self._cmd_go,
            "move": self._cmd_go,
            "north": lambda _: self._cmd_go(["north"]),
            "south": lambda _: self._cmd_go(["south"]),
            "east": lambda _: self._cmd_go(["east"]),
            "west": lambda _: self._cmd_go(["west"]),
            "look": self._cmd_look,
            "inspect": self._cmd_inspect,
            "take": self._cmd_take,
            "get": self._cmd_take,
            "inventory": self._cmd_inventory,
            "inv": self._cmd_inventory,
            "i": self._cmd_inventory,
            "equip": self._cmd_equip,
            "use": self._cmd_use,
            "attack": self._cmd_attack,
            "fight": self._cmd_attack,
            "help": self._cmd_help,
            "quit": self._cmd_quit,
        }

    @property
    def current_room(self) -> Room:
        return self.world[self.player.current_room_id]

    def run(self) -> None:
        self._print_banner()
        self._cmd_look([])

        while self.game_running:
            if not self.player.is_alive:
                self._handle_game_over()
                break

            try:
                line = input(f"\n{UI.CYAN}[{self.player.hp}/{self.player.max_hp} HP] ❯ {UI.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{UI.YELLOW}Session suspended. Exiting...{UI.RESET}")
                break

            if not line:
                continue

            self._process_input(line)

    def _process_input(self, raw_input: str) -> None:
        tokens = raw_input.lower().split()
        verb = tokens[0]
        args = tokens[1:]

        handler = self.commands.get(verb)
        if handler:
            handler(args)
        else:
            print(f"{UI.RED}Unrecognized command: '{verb}'. Type 'help' for available actions.{UI.RESET}")

    # --- Commands ---

    def _cmd_look(self, args: List[str]) -> None:
        room = self.current_room
        UI.divider()
        print(f"{UI.BOLD}{UI.MAGENTA}{room.title}{UI.RESET}")
        UI.print_wrapped(room.description)

        # Print items in room
        if room.items:
            item_names = [f"{UI.GREEN}{i.name}{UI.RESET}" for i in room.items.values()]
            print(f"\nItems visible: {', '.join(item_names)}")

        # Print active threat
        if room.enemy and room.enemy.is_alive:
            print(f"\n{UI.RED}{UI.BOLD}⚠ A hostile {room.enemy.name} stands before you!{UI.RESET}")
            UI.print_wrapped(room.enemy.description, prefix="  ")

        # Exits list
        visible_exits = [
            f"{direction} (locked)" if direction in room.locked_exits else direction
            for direction in room.exits
        ]
        print(f"\n{UI.DIM}Obvious exits: {', '.join(visible_exits) if visible_exits else 'None'}{UI.RESET}")
        UI.divider()

    @staticmethod
    def _normalize_item_name(name: str) -> str:
        return "".join(character for character in name.lower() if character.isalnum())

    @classmethod
    def _item_matches(cls, query: str, item_id: str, item: Item) -> bool:
        normalized_query = cls._normalize_item_name(query)
        return (
            normalized_query in cls._normalize_item_name(item_id)
            or normalized_query in cls._normalize_item_name(item.name)
        )

    def _cmd_go(self, args: List[str]) -> None:
        if not args:
            print(f"{UI.YELLOW}Specify a direction: north, south, east, west.{UI.RESET}")
            return

        direction = args[0]
        room = self.current_room

        # Check if enemy blocks path
        if room.enemy and room.enemy.is_alive:
            print(f"{UI.RED}The {room.enemy.name} blocks your path! You must defeat it or flee.{UI.RESET}")
            return

        # Check if exit exists
        if direction not in room.exits:
            print(f"{UI.RED}You cannot travel {direction} from here.{UI.RESET}")
            return

        # Check if exit is locked
        required_key = room.locked_exits.get(direction)
        if required_key:
            if required_key in self.player.inventory:
                key_item = self.player.inventory[required_key]
                print(f"{UI.GREEN}You unlock the gate using your {key_item.name}!{UI.RESET}")
                del room.locked_exits[direction]  # Unlocked permanently
            else:
                required_item_name = required_key.replace("_", " ").title()
                print(
                    f"{UI.YELLOW}The path to the {direction} is sealed. "
                    f"You need the {required_item_name}.{UI.RESET}"
                )
                return

        # Transition
        self.player.current_room_id = room.exits[direction]
        self._cmd_look([])

    def _cmd_take(self, args: List[str]) -> None:
        if not args:
            print(f"{UI.YELLOW}What do you want to take?{UI.RESET}")
            return

        target_name = " ".join(args).lower()
        room = self.current_room

        # Match names consistently whether spaces, underscores, or punctuation are used.
        matched_id: Optional[str] = None
        for item_id, item in room.items.items():
            if self._item_matches(target_name, item_id, item):
                matched_id = item_id
                break

        if not matched_id:
            print(f"{UI.YELLOW}There is no '{target_name}' here.{UI.RESET}")
            return

        picked = room.items.pop(matched_id)
        self.player.inventory[picked.id] = picked
        print(f"{UI.GREEN}Obtained: {picked.name}.{UI.RESET}")

        # Auto-equip if player has no weapon
        if picked.item_type == ItemType.WEAPON and not self.player.equipped_weapon:
            self.player.equipped_weapon = picked
            print(f"{UI.CYAN}Auto-equipped {picked.name} (+{picked.damage_bonus} ATK).{UI.RESET}")

    def _cmd_inventory(self, args: List[str]) -> None:
        if not self.player.inventory:
            print(f"{UI.DIM}Your pack is empty.{UI.RESET}")
            return

        print(f"\n{UI.BOLD}Inventory:{UI.RESET}")
        for item in self.player.inventory.values():
            status = f" {UI.CYAN}(Equipped){UI.RESET}" if item == self.player.equipped_weapon else ""
            print(f"  • {UI.GREEN}{item.name:<18}{UI.RESET} - {item.description}{status}")

    def _cmd_equip(self, args: List[str]) -> None:
        if not args:
            print(f"{UI.YELLOW}Specify which weapon to equip.{UI.RESET}")
            return

        target = " ".join(args).lower()
        for item in self.player.inventory.values():
            if self._item_matches(target, item.id, item) and item.item_type == ItemType.WEAPON:
                self.player.equipped_weapon = item
                print(f"{UI.GREEN}Equipped {item.name}. Total Attack: {self.player.total_damage}.{UI.RESET}")
                return

        print(f"{UI.RED}No weapon matching '{target}' found in your inventory.{UI.RESET}")

    def _cmd_use(self, args: List[str]) -> None:
        if not args:
            print(f"{UI.YELLOW}Use what item?{UI.RESET}")
            return

        target = " ".join(args).lower()
        matched_id = None
        for item_id, item in self.player.inventory.items():
            if self._item_matches(target, item_id, item):
                matched_id = item_id
                break

        if not matched_id:
            print(f"{UI.RED}You do not possess that item.{UI.RESET}")
            return

        item = self.player.inventory[matched_id]

        if item.item_type == ItemType.CONSUMABLE and item.heal_amount > 0:
            healed = self.player.heal(item.heal_amount)
            del self.player.inventory[matched_id]
            print(f"{UI.GREEN}You drink {item.name}. Recovered {healed} HP! ({self.player.hp}/{self.player.max_hp}){UI.RESET}")
            return

        if item.item_type == ItemType.KEY:
            for direction, required_key in list(self.current_room.locked_exits.items()):
                if required_key == item.id:
                    del self.current_room.locked_exits[direction]
                    print(f"{UI.GREEN}You unlock the {direction} gate using your {item.name}.{UI.RESET}")
                    return
            print(f"{UI.YELLOW}There is no lock here that fits the {item.name}.{UI.RESET}")
            return

        if item.use_effect == "break_barrier":
            for direction in list(self.current_room.locked_exits):
                del self.current_room.locked_exits[direction]
                print(f"{UI.GREEN}{item.name} flares with light and breaks the barrier to the {direction}!{UI.RESET}")
                return
            print(f"{UI.YELLOW}{item.name} glows warmly, but there is no barrier here to break.{UI.RESET}")
            return

        print(f"{UI.YELLOW}Using {item.name} has no immediate effect right now.{UI.RESET}")

    def _cmd_inspect(self, args: List[str]) -> None:
        if not args:
            print(f"{UI.YELLOW}Inspect what?{UI.RESET}")
            return

        target = " ".join(args).lower()
        # Check inventory
        for item in self.player.inventory.values():
            if self._item_matches(target, item.id, item):
                print(f"{UI.BOLD}{item.name}{UI.RESET}: {item.description}")
                return

        # Check room items
        for item in self.current_room.items.values():
            if self._item_matches(target, item.id, item):
                print(f"{UI.BOLD}{item.name}{UI.RESET}: {item.description}")
                return

        # Check enemy
        enemy = self.current_room.enemy
        if enemy and (target in enemy.name.lower()):
            print(f"{UI.BOLD}{enemy.name}{UI.RESET}: {enemy.description} [HP: {enemy.hp}/{enemy.max_hp}]")
            return

        print(f"{UI.YELLOW}Nothing matching '{target}' to inspect.{UI.RESET}")

    def _cmd_attack(self, args: List[str]) -> None:
        room = self.current_room
        enemy = room.enemy

        if not enemy or not enemy.is_alive:
            print(f"{UI.DIM}There is nothing hostile here to attack.{UI.RESET}")
            return

        # Player Turn: Base damage +/- 2 variation
        variance = self.rng.randint(-2, 2)
        player_hit = max(1, self.player.total_damage + variance)
        dealt = enemy.take_damage(player_hit)

        print(f"\n{UI.GREEN}You strike the {enemy.name} for {dealt} damage! ({enemy.hp}/{enemy.max_hp} HP remaining){UI.RESET}")

        # Check Victory
        if not enemy.is_alive:
            print(f"{UI.BOLD}{UI.GREEN}✔ You vanquished the {enemy.name}!{UI.RESET}")
            if enemy.loot:
                room.items[enemy.loot.id] = enemy.loot
                print(f"{UI.YELLOW}The creature dropped: {enemy.loot.name}.{UI.RESET}")

            # Check final victory condition
            if enemy.name == "Gargoyle Warden":
                self._handle_game_win()
            return

        # Enemy Turn
        enemy_variance = self.rng.randint(-1, 2)
        enemy_hit = max(1, enemy.base_damage + enemy_variance)
        sustained = self.player.take_damage(enemy_hit)
        print(f"{UI.RED}The {enemy.name} retaliates, striking you for {sustained} damage!{UI.RESET}")

    def _cmd_help(self, args: List[str]) -> None:
        print(f"\n{UI.BOLD}Available Commands:{UI.RESET}")
        commands_help = [
            ("go <direction>", "Travel (or type north, south, east, or west directly)"),
            ("look", "Examine current location in detail"),
            ("take <item>", "Pick up an object (the Rusty Dagger auto-equips)"),
            ("inspect <target>", "Read details about an item or foe"),
            ("inventory / i", "Display all items currently held"),
            ("equip <weapon>", "Equip a weapon from your pack"),
            ("use <item>", "Drink a potion, use a key at a locked gate, or use the Sun Amulet"),
            ("attack / fight", "Strike the hostile creature in the room"),
            ("quit", "Abandon journey and exit"),
        ]
        for cmd, desc in commands_help:
            print(f"  {UI.CYAN}{cmd:<18}{UI.RESET} : {desc}")

    def _cmd_quit(self, args: List[str]) -> None:
        print(f"{UI.YELLOW}Farewell, traveler.{UI.RESET}")
        self.game_running = False

    def _handle_game_over(self) -> None:
        UI.divider()
        print(f"\n{UI.RED}{UI.BOLD}YOU HAVE FALLEN...{UI.RESET}")
        print("Your bones join the cold foundation of the crypt.")
        UI.divider()
        self.game_running = False

    def _handle_game_win(self) -> None:
        UI.divider()
        print(f"\n{UI.GREEN}{UI.BOLD}★ VICTORY ACHIEVED ★{UI.RESET}")
        print(
            "With the Gargoyle Warden shattered into gravel, the grand archway unseals.\n"
            "Golden dawn spills across your face as you emerge victorious onto the overland plains!"
        )
        UI.divider()
        self.game_running = False

    def _print_banner(self) -> None:
        banner = f"""
{UI.BOLD}{UI.CYAN}╔══════════════════════════════════════════════════════════════════════════╗
║               CHRONICLES OF THE SUNKEN CRYPT : ENGINE v2.0              ║
╚══════════════════════════════════════════════════════════════════════════╝{UI.RESET}
Type {UI.BOLD}'help'{UI.RESET} anytime to review available commands.
"""
        print(banner)


# =====================================================================
# Main Entry Point
# =====================================================================

if __name__ == "__main__":
    game = GameEngine()
    game.run()
