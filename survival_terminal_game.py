'''
Objective of the game:
Use resources to reach the endpoint alive

Context:
The world has experienced an ice age, and you are stranded in a random northern European town - with little resources and food. You have to reach a warmer area, somewhere like Casablanca to survive.

Node logic:
Hardcoded nodes (locations) - and the player can travel to certain nodes from certain starting nodes.
'''

#all temperatures in Celcius

MAX_HEALTH = 10
MAX_FOOD = 10
START_BODY_TEMP = 37.0
FINAL_LOCATION = "Casablanca Desert Fortress"
SIDEBAR_WIDTH = 30

#Whether the interface has borders.
TOP_INFO_BORDERS = "bold red"
SIDEBAR_BORDERS = "red"

# How long each stage takes to pass
REAL_TIME_PER_STAGE = 0.5

#Hotbar width- affects dialogue box
DIALOGUE_WIDTH = 80
HOTBAR_SPACING = 15

USABLE_WIDTH = DIALOGUE_WIDTH - 4 # the usable width in the dialogue box is the dialogue wdith - borders and padding (2 + 2)

#Symbols that may change
FULL_HEART_SYMBOL = "❤️ "
HALF_HEART_SYMBOL = "💗"
EMPTY_HEART_SYMBOL = "🩶 "

FULL_FOOD_SYMBOL = "🍖"
HALF_FOOD_SYMBOL = "🍗"
EMPTY_FOOD_SYMBOL = "🦴"

#Number of rows for the dialogue box
DIALOGUE_TEXT_ROWS = 15

# the mapping of colours for rarity 
RARITY_COLOURS = {
    "Common": "cyan",
    "Uncommon": "green",
    "Rare": "dark_orange",
    "Epic": "purple",
    "Legendary": "yellow",
    "Unique": "magenta",
    "Quest Reward": "bold red",
    "Quest Special": "bold red",
    "Quest Item": "gold1"
}

# Inventory limits of both inventories
BACKPACK_LIMIT = 8
SATCHEL_LIMIT = 30

# How much health you get when eating a food with a certain food gain value
FOOD_TO_HEALTH_CONVERSION = 0.5 #50%

# Warm food lasting stages (how many stages does warm food stay warm for?)
WARM_FOOD_LASTING_STAGES = 2

# What shelter is required minimum to have your food become warm (no need to cook the food for it to be warm - but just staying in a warm place)
WARM_FOOD_SHELTERS = ["Good Shelter", "Decent Shelter"]

# Maps types of shelters to what body temp they get you up to at maximum
SHELTER_MAX_TEMPERATURES = {
    "Good Shelter":37.0,
    "Decent Shelter":36.0,
    "Mediocre Shelter":34.0,
    "Poor Shelter":31.5,
    "No Shelter": "N/A"
}

# Temperature drop coefficient
TEMPERATURE_CHANGE_COEFFICIENT = 0.20 #you drop 20% of temperature between your current temperature and the feels like temperature

# Cutscene Script Actions
PAUSE = "[pause]"
SEPARATOR = "[separator]"
CHOICE_START = "[choice]"
CHOICE_END = "[/choice]"

'''Note: 

To print messages inside the dialogue box, use log().

Finally, to print messages outside (and below) the dialogue box, use print() as normal (for things such as input text.)
'''

# Importing stuff
from time import sleep
from rich import print
from rich.columns import Columns
from rich.panel import Panel
from random import choice, randint, shuffle
from datetime import date, timedelta
from rich.console import Console, Group
from rich.align import Align
import sys
import math
import re

# class Player helps store information, and stats of the player
class Player:
    def __init__(self):
        self.health = MAX_HEALTH
        self.food_level = MAX_FOOD
        self.body_temp = START_BODY_TEMP
        self.hypothermia_status = "None"

        # Smaller fixed slot amount, but for regular survival items. (backpack)
        self.backpack = []
        self.satchel = []
        self.clothing = [None, None, None, None]

    def take_damage(self, amount):
        '''Inflicts a certain amount of damage, reducing health. Does not allow health to go below 0.'''
        #ensure health > 0
        self.health = (self.health - amount) if (self.health - amount) > 0 else 0
        print(f"Player took {amount} damage!")

    def food_decrease(self, amount):
        '''Decreases the food level by an amount. Does not allow food level to go below 0, and if so, reduces health by 1.'''
        if self.food_level >= amount:
            self.food_level -= amount
        else:
            deficit = abs(self.food_level - amount)
            self.food_level = 0 #can't be below
            self.take_damage(deficit)
            print(f"You are very hungry...")

    def recover_health(self, amount):
        '''Increase health by a certain amount, but not over 10.'''
        if amount + self.health > MAX_HEALTH:
            self.health = MAX_HEALTH
        else:
            self.health += amount

    def food_increase(self, amount):
        '''Increase food level by a certain amount, but not over the maximum.'''
        if amount + self.food_level > MAX_FOOD:
            self.food_level = MAX_FOOD
        else:
            self.food_level += amount

    def is_alive(self):
        '''Returns True if the player is alive.'''
        if self.health > 0:
            return True
        return False

class Location:
    def __init__(self, name, distance_left, temp, description, shelter_status, accessible_locations):
        self.name = name
        self.distance_left = distance_left
        self.temp = temp
        self.description = description

        self.shelter_status = shelter_status
        
        # a dictionary with the accessible location with a nested dictionary to show more info (Distance to that location, the direction, the stages of the day taken, and the requirements)
        self.accessible_locations = accessible_locations 

class Item:
    # Some things default to default states
    def __init__(self, item_name, description, rarity, item_type, max_durability=1, current_durability=1, quantity_remaining=1, is_quest_item=False, important_information=None):
        # The normal things needed for an item
        self.item_name = item_name
        self.description = description
        self.rarity = rarity
        self.item_type = item_type

        self.max_durability = max_durability
        self.current_durability = current_durability # or uses for a consumable

        self.quantity_remaining = quantity_remaining
        

        self.is_quest_item = is_quest_item # if yes, it cannot be discarded and it is placed into the 30 slot inventory


        # makes sure each item gets a separate dictionary
        self.important_information = important_information if important_information is not None else {} #stores special states for items (like whether the note has been tampered or not)

    def return_coloured_name(self, item):
        '''Returns a coloured version of the item name based on its rarity.'''
        colour = RARITY_COLOURS.get(item.rarity, "white") #fallback becomes white
        return f"[{colour}]{self.item_name}[/{colour}]"

    def reduce_durability(self, amount):
        '''Reduces the durability or uses of that item by a certain amount.'''

        # decrement while maintaining above 0
        self.current_durability = max(0, self.current_durability - amount)

    def get_durability_display(self):
        '''Gets the durability display with a colour.'''

        if self.max_durability <= 0: #prevent div by 0
            return "[dim]N/A[/dim]"

        percentage_durability = self.current_durability / self.max_durability

        if percentage_durability >= 0.75:
            colour = "bold green"
        elif percentage_durability >= 0.50:
            colour = "yellow"
        elif percentage_durability >= 0.25:
            colour = "dark_orange"
        else:
            colour = "dim red" 

        # Returns the colour version of the durability
        return f"[{colour}]{self.current_durability}/{self.max_durability}[/{colour}]" 

    def get_stat(self, stat_name, fallback_value):
        '''Returns a stat of an item from important information (IF IT EXISTS). Otherwise, return a fallback value.'''

        return self.important_information.get(stat_name, fallback_value)

class Quest:
    def __init__(self, title, type, description, max_progress, progress_label):
        self.title = title
        self.type = type # "Tutorial Quest", "Optional Quest", "Main Quest"
        self.description = description
        self.current_progress = 0
        self.max_progress = max_progress 

        self.progress_label = progress_label #like a string or whatever (e.g. "parts collected", "screws undone", "In progress")

        self.is_completed = False

    def complete_quest(self):
        '''Updates quest status to completed.'''

        self.is_completed = True

    def advance_progress(self, amount):
        '''Advances the progress a certain amount.'''

        self.current_progress += amount

        if self.current_progress >= self.max_progress: #if you did the progress needed
            self.complete_quest()
            self.progress_label = "[green]Quest Complete![/green]"

    def get_quest_display(self):
        '''Gets a string for the quest display itself. (E.g. Main Quest: Collect Jeremy's body.)'''

        return f"[bold][yellow]{self.type}[/yellow]\n{self.title}[/bold]"

    def get_progress_display(self):
        '''Gets a string for the display for your progress. (E.g. 2/5 coins collected)'''
        if self.progress_label == "In Progress":
            return f"[dim][yellow]{self.progress_label}[/yellow][dim]"

        else:
            return f"[[dim][yellow]{self.current_progress}/{self.max_progress} {self.progress_label}[/yellow][/dim]]"

class Game:
    def __init__(self):
        self.player = Player()
        self.day = 1
        self.date = date.today() #starts the date at today's date
        self.formatted_date = self.date.strftime("%a, %b %d") 
        self.current_stage = 'Morning'
        self.weather = "Clear"
        self.environment_temp = -25.0
        self.feels_like_temp = -25.0
        self.current_location = "Permafrost Camp" #player starts at Permafrost Camp
        self.current_shelter_status = "Poor Shelter"

        self.distance_left = 3500 #km

        # Quest
        self.current_quest = None

        # E-ink slate
        self.slate_entries = []

        #Not game related (directly)
        self.past_dialogue = [" "] * 5 #when the game starts, there is no past dialogue
        self.current_message_block = [] #Preferably don't use the log_chunk thing
        self.action_menu_open = False
        self.is_resting = False
        self.is_travelling = False

        self.typewriter_override = False

        # Quest specifics
        self.left_camp_before = False

        # Settings - first item in list stores the displayed name, 2nd stores the state
        self.settings = {
            "typewriter":{
                "Display Name":"Typewriter", 
                "Status":True,

                "Available Options":{
                    "On":True,
                    "Off":False
                }},

            "typewriter_speed":{
                            "Display Name":"Typewriter Speed", 
                            "Status":'0.02',
                            
                            "Available Options":{
                                "Ultra Fast":0.01,
                                "Fast":0.02,
                                "Normal":0.03,
                                "Slow":0.05,
                                "Slug":0.08
                            }},

            "temp_unit":{
                            "Display Name":"Temperature Unit", 
                            "Status":"°C",
                            
                            "Available Options":{
                                "Celsius":"°C",
                                "Fahrenheit":"°F",
                                "Kelvin":"°K"
                            }}
        }

        # a dictionary of locations / nodes - to add new locations: -> add name, temp, distance to finish, accessible locations (which is a dictionary)
        self.locations = {"Permafrost Camp" : Location("Permafrost Camp", 3500, -25.0, "A cold, brutal camp with scraps of resources and an abandoned shelter.", "Poor Shelter",
                                                 {"Lakeside Castle Ruins" : 
                                                  {
                                                    "distance_to" : 25,
                                                    "direction_to" : "Southwest",
                                                    "stages_needed" : 1, 
                                                    "requirements" : None
                                                 },
                                                 
                                                  "Icy Car Repair Depot" : 
                                                  {
                                                    "distance_to" : 65,
                                                    "direction_to" : "North-northwest",
                                                    "stages_needed" : 3,
                                                    "requirements" : None
                                                  }
                                                 }),
                        #for each location on the map, add the things above here

                        #--------------------------------------------------------------------
                        "Lakeside Castle Ruins" : Location("Lakeside Castle Ruins", 3400, -24.0, "A castle ruins by the frozen lake. No signs of life here.", "No Shelter",
                                                 {"Permafrost Camp" : 
                                                  {
                                                    "distance_to" : 25,
                                                    "direction_to" : "Northeast",
                                                    "stages_needed" : 1,
                                                    "requirements" : None
                                                  },

                                                "Valley Camp 02" : 
                                                {
                                                "distance_to" : 100,
                                                "direction_to" : "West-southwest",
                                                "stages_needed" : 4,
                                                "requirements" : None
                                                },

                                                "Barren Highlands" : 
                                                {
                                                "distance_to" : 10,
                                                "direction_to" : "Northwest",
                                                "stages_needed" : 1,
                                                "requirements" : "Headwear"
                                                },
                                                }

                                                ),

                        #--------------------------------------------------------------------
                        "Icy Car Repair Depot" : Location("Icy Car Repair Depot", 3550, -26.0, "A car repair depot operated by Jeremy, a local survivor. Locals say he's a talent.", "Good Shelter",
                                                 {"Permafrost Camp" : 
                                                  {
                                                    "distance_to" : 65,
                                                    "direction_to" : "South-southeast",
                                                    "stages_needed" : 3,
                                                    "requirements" : None
                                                 },

                                                 "Blizzard Graveyard" : 
                                                  {
                                                    "distance_to" : 15,
                                                    "direction_to" : "North-northwest",
                                                    "stages_needed" : 1,
                                                    "requirements" : None
                                                 },

                                                }),

                        #--------------------------------------------------------------------
                        "Blizzard Graveyard" : Location("Blizzard Graveyard", 3600, -27.0, "A haunting, frozen graveyard with hundreds and hundreds of snow covered graves.", "No Shelter",
                                                    {"Icy Car Repair Depot" : 
                                                    {
                                                    "distance_to" : 15,
                                                    "direction_to" : "South-southeast",
                                                    "stages_needed" : 1,
                                                    "requirements" : None
                                                    },

                                                    "Abandoned Polar Bunker 01" : 
                                                  {
                                                    "distance_to" : 45,
                                                    "direction_to" : "North",
                                                    "stages_needed" : 2,
                                                    "requirements" : None
                                                 },

                                                 "Polar Rail Summit Station" : 
                                                {
                                                    "distance_to" : 75,
                                                    "direction_to" : "West",
                                                    "stages_needed" : 3,
                                                    "requirements" : ["Headwear", "Any rail pass"]
                                                },
                                                }),

                        #--------------------------------------------------------------------
                        "Abandoned Polar Bunker 01" : Location("Abandoned Polar Bunker 01", 3650, -30.0, "Seemingly abandoned many months ago, though still sturdy and functional.", "Mediocre Shelter",
                                                    {"Blizzard Graveyard" : 
                                                     {
                                                    "distance_to" : 45,
                                                    "direction_to" : "South",
                                                    "stages_needed" : 2,
                                                    "requirements" : None
                                                },
                                                }),

                        #--------------------------------------------------------------------
                        "Valley Camp 02" : Location("Valley Camp 02", 3300, -25.0, "Where previous survivors went to shelter from the cold.", "Mediocre Shelter",
                                                    {"Lakeside Castle Ruins" : 
                                                     {
                                                    "distance_to" : 100,
                                                    "direction_to" : "East-northeast",
                                                    "stages_needed" : 4,
                                                    "requirements" : None
                                                },

                                                "Barren Highlands" : 
                                                {
                                                    "distance_to" : 120,
                                                    "direction_to" : "North",
                                                    "stages_needed" : 5,
                                                    "requirements" :"Headwear"
                                                }
                                                }),

                        #--------------------------------------------------------------------
                        "Barren Highlands" : Location("Barren Highlands", 3420, -33.0, "You might find a random rail engineer here, living inside a bunker. It's freezing up here.", "Decent Shelter",
                                                    {"Lakeside Castle Ruins" : 
                                                     {
                                                    "distance_to" : 10,
                                                    "direction_to" : "Southeast",
                                                    "stages_needed" : 1,
                                                    "requirements" : None #to leave barren highlands you don't need headwear
                                                },

                                                "Valley Camp 02" : 
                                                {
                                                    "distance_to" : 120,
                                                    "direction_to" : "South",
                                                    "stages_needed" : 5,
                                                    "requirements" : None #to leave barren highlands you don't need headwear
                                                },

                                                "Polar Rail Summit Station" : 
                                                {
                                                    "distance_to" : 75,
                                                    "direction_to" : "North",
                                                    "stages_needed" : 3,
                                                    "requirements" : ["Headwear", "Any rail pass"]
                                                },
                                                }),

                        #--------------------------------------------------------------------
                        "Polar Rail Summit Station" : Location("Polar Rail Summit Station", 3500, -37.0, "Your hands will freeze off without being inside a warm train, with a train pass.", "No Shelter",
                                                    {"Blizzard Graveyard" : 
                                                     {
                                                    "distance_to" : 75,
                                                    "direction_to" : "East",
                                                    "stages_needed" : 3,
                                                    "requirements" : "Any rail pass" #to leave barren highlands you don't need headwear
                                                },

                                                "Barren Highlands" : 
                                                {
                                                    "distance_to" : 75,
                                                    "direction_to" : "South",
                                                    "stages_needed" : 3,
                                                    "requirements" : "Any rail pass" #to leave barren highlands you don't need headwear
                                                }
                                                })
                        }

    def get_coloured_name(self, item_name, rarity):
        '''Returns a coloured version of any name based on its rarity.'''
        colour = RARITY_COLOURS.get(rarity.title(), "white") #fallback becomes white
        return f"[{colour}]{item_name}[/{colour}]"

    def open_settings_menu(self, mode="normal"):
        '''Open a settings menu to allow user to modify settings.'''

        # Map inputs into setting_keys 
        valid_settings = {

            "1":"typewriter",
            "typewriter":"typewriter",


            "2":"typewriter_speed",
            "typewriter speed":"typewriter_speed",

            "3":"temp_unit",
            "temperature unit":"temp_unit"

        }

        error_message = ""

        while True:
            if mode == "normal":
                self.refresh_screen()
            else:
                self.clear_screen()
            print(f"[bold red]Settings[/bold red]\n")

            if error_message != "": #if there is an error message
                print(f"\n[bold red]{error_message}[/bold red]") #prints error message in red

            for setting_key in self.settings:

                display_name = self.settings[setting_key]["Display Name"]
                status = self.settings[setting_key]["Status"]

                if status in [True, False]: #if it is a boolean / toggleable
                     print(self.generate_setting_display(setting_key)) #prints the toggled display
                else:
                     print(f"{display_name} - {status}")

            setting_choice = input("\nEnter the setting number or name you want to change.\n").lower().strip()

            if setting_choice in valid_settings.keys():
                chosen_option = valid_settings[setting_choice] #chosen option is the setting's key
                break

            error_message = f"That is not a setting you can change."

        if mode == "normal":
            self.refresh_screen()
        else:
            self.clear_screen()

        # Conditions for each setting

        # Get info about the setting (chosen_option is the setting_key)
        display_name = self.settings[chosen_option]["Display Name"]
        status = self.settings[chosen_option]["Status"]
        available_options = self.settings[chosen_option]["Available Options"]

        # Setting 1 type -> for any on / off settings

        if status in [True, False]: # add or statements for any toggleable (true/false) settings
            self.toggle_setting(chosen_option) #Inverts the setting
            new_status = self.settings[chosen_option]["Status"]

            status_name = self.find_key_from_value(available_options, new_status) #Gets the status name from the status 

            print(f"You toggled {status_name.lower()} {display_name.lower()}. ")
            
        else: # Setting 2 type -> string or number (many options) based settings

            error_message = ""

            while True:
                if mode == "normal":
                    self.refresh_screen()
                else:
                    self.clear_screen()
                print(f"[bold red]{display_name}[/bold red]\n")

                if error_message != "": #if there is an error message
                    print(f"\n[bold red]{error_message}[/bold red]") #prints error message in red

                current_setting_name = "current" #initialise the var
                print(f"You have the following options:")
                for option in available_options:
                    print(f"{option} - {available_options[option]}") #shows the name and the setting

                    if str(status).strip() == str(available_options[option]).strip(): #finds the current setting name
                        current_setting_name = option

                setting_choice = input("\nEnter the new setting you would like to have. (The setting name or value) \n").strip()
                origin_status = status

                cleaned_choice = self.clean_value(setting_choice)

                # case-insensitive lookup for matching either the key (e.g. "Fast") or value (e.g. "0.02")
                matched_key = None
                for opt_key, opt_value in available_options.items():
                    if cleaned_choice.lower() == self.clean_value(opt_key):
                        matched_key = opt_key
                        break
                    elif cleaned_choice.lower() == self.clean_value(opt_value):
                        matched_key = opt_key
                        break

                if matched_key is not None: # if it matched a valid option
                    
                    self.settings[chosen_option]["Status"] = available_options[matched_key] #changes status to the right value
                    new_value = self.settings[chosen_option]["Status"]

                    print(f"You changed {display_name.lower()} from {current_setting_name.lower()} ({origin_status}) to {matched_key.lower()} ({new_value}).")

                    break #exit loop

                else:
                    error_message = f"That is not a option you can change to."
                    
        # Call the settings menu function again if the user wants to keep adjusting settings
        self.custom_sleep(1)
        
        # self.refresh_screen()

        print("[white]Exit or continue changing settings?[/white] ([bold red][u]E[/u][/bold red]xit / [bold green][u]C[/u][/bold green]ontinue): ", end="")
        setting_exit = input()

        if setting_exit.upper().strip() == "E":
            if mode == "normal":
                return None # exit
            else:
                return "Continue"
        else:
            self.open_settings_menu()

    def clean_value(self, value):
        '''Removes degree symbol from value.'''
        return str(value).lower().replace("°", "").replace("deg", "").strip()

    def find_key_from_value(self, dictionary, value):
        '''From a dictionary, it finds the key from a value - provided all values are UNIQUE.
        Used in the settings menu.'''
        try:
            key = list(dictionary.keys())[list(dictionary.values()).index(value)]
        except:
            return "No key found"
        return key

    def toggle_setting(self, setting):
        '''Works only for enabled / disabled setting types. Toggles them to the opposite version.'''

        self.settings[setting]["Status"] = not self.settings[setting]["Status"] #inverts

    def generate_setting_display(self, setting_key):
        '''Generates a setting display to be in the settings menu.'''

        setting_name = self.settings[setting_key]["Display Name"]

        status = self.settings[setting_key]["Status"]
        
        symbol = "🟢 Enabled" if status else "🔴 Disabled"

        return f"{setting_name} - {symbol}"

    def advance_day(self):
        '''Advances the day counter by 1.'''
        self.day += 1
        self.advance_date()

    def advance_date(self):
        '''Changes the date to match the advance in the day.'''
        self.date = self.date + timedelta(days=1)
        self.formatted_date = self.date.strftime("%a, %b %d") #updates the formatted date
        
    def advance_stage(self):
        '''Advances to the next stage in the day - there are 3 stages in the day - morning, afternoon, and night.
        Advancing a stage has a change to randomise the weather again. Updates the feels like temp as well.'''
        stages = ['Morning', 'Afternoon','Night']
        index = (stages.index(self.current_stage) + 1) % 3 #gets the right index, but makes sure its between 1-3

        self.current_stage = stages[index]
        if self.current_stage == "Morning": #if an entire day was skipped (went from Night -> Morning), then advance the day
            self.advance_day()

        if randint(0,2) == 1: #1/3 chance to randomise weather
            self.randomise_weather()

        self.update_feels_like_temp()

        # Update body temp
        self.body_temperature_update()

    def advance_stages(self, stages):
        '''Advances many stages.'''
        for _ in range(stages):
            self.advance_stage()

    def body_temperature_update(self):
        '''Updates your body temperature through a realistic (Newton's Law of cooling) way to slowly make your temperature creep to the FEELs like temperature.'''

        # If you rest, temperature goes down or up by less (15% less)
        current_coefficient = (TEMPERATURE_CHANGE_COEFFICIENT - 0.15) if self.is_resting or self.is_travelling else TEMPERATURE_CHANGE_COEFFICIENT
        
        # first calculate the total warmth of your clothing
        total_warmth = 0.0
        for clothing_piece in self.player.clothing:
            if clothing_piece is not None:
                total_warmth += clothing_piece.get_stat("Warmth", 0.0)

        # get the quality of your shelter
        shelter_status = self.get_location_shelter_status()

        # map the shelter quality to your max temperature that you creep to while in a shelter
        if shelter_status != "No Shelter":
            shelter_temperature = SHELTER_MAX_TEMPERATURES[shelter_status]

            # heat up (or cool down, if you had a bad shelter) 2x faster than you cool down without a shelter

            temperature_difference = shelter_temperature - self.player.body_temp #positive if the shelter temperature is hotter than body temp, but negative otherwise

            temperature_change = temperature_difference * current_coefficient * 2

            # decreases player temp to match closer to the shelter's temperature

            self.player.body_temp += temperature_change

        else: # Use Newton's cooling law for temperature change - since you have no shelter
            temperature_difference = abs(self.feels_like_temp - self.player.body_temp)
            temperature_loss =  (temperature_difference * current_coefficient) * (1.0 - total_warmth)

            self.player.body_temp -= temperature_loss


        # Apply hypothermia check to change health

        body_temperature = self.player.body_temp

        if body_temperature >= 36:  
            self.player.hypothermia_status = "None"

        elif body_temperature >= 35:
            self.player.hypothermia_status = "Acute"
            if not (self.is_resting or self.is_travelling): # if player not resting or travelling
                self.log("You feel slightly hungrier due to your acute hypothermia and slight shivering.")
            self.player.food_decrease(0.5)

        elif body_temperature >= 32:
            self.player.hypothermia_status = "Mild"
            if not (self.is_resting or self.is_travelling): # if player not resting or travelling
                self.log("You feel slightly hungrier due to your mild hypothermia and shivering.")
            self.player.food_decrease(1)

        elif body_temperature >= 28:
            self.player.hypothermia_status = "Severe"
            if not (self.is_resting or self.is_travelling): # if player not resting or travelling
                self.log("You check your hands and feet. You have severe frostbite and hypothermia. Ouch!")
            self.player.take_damage(2)

        else:
            self.player.hypothermia_status = "Critical"
            if not (self.is_resting or self.is_travelling): # if player not resting or travelling
                self.log("You are on the brink of collapse, in critical condition because of the cold.")
            self.player.take_damage(5)

        if body_temperature > 37.0:
            self.player.body_temp = 37.0

    def get_location_shelter_status(self):
        '''Returns the name of the shelter status of your location (Good Shelter, Decent Shelter, Mediocre Shelter, Poor Shelter, No Shelter)'''

        return self.locations[self.current_location].shelter_status

    def clear_screen(self):
        '''Clears the screen.'''
        interface = Console()
        interface.clear()

    def randomise_weather(self):
        '''Randomises weather, but ensures it is realistic to the current environmental temperature.'''
        #note: if changing / adding possible weather conditions, remember to change indexes if needed
        possible_weather = ["Rain", "Clear", "Cloudy", "Snowstorm", "Strong Winds", "Snow", "Hail"]

        if self.environment_temp > 4: #if its relatively warmer
            index = randint(0,2) #excludes snow
            
        else: #excludes rain
            index = randint(1, len(possible_weather) - 1)

        self.weather = possible_weather[index]

    def get_weather_symbol(self):
        '''Returns the correct emoji based on current weather.'''
        symbol_matching = {"Rain":"💧", "Clear":"🌞", "Cloudy":"⛅", "Snowstorm":"🏔️", "Strong Winds":"🍃", "Snow":"⛄", "Hail":"🧊"} #some emojis have a space after due to a visual bug

        return symbol_matching[self.weather]

    def update_feels_like_temp(self):
        '''Gets the rough temperature felt by the player - affected by weather, time of day, and environmental temperature.'''
        weather_effects = {"Rain":-3, "Clear":2, "Cloudy":0, "Snowstorm":-4, "Strong Winds":-2, "Snow":-6, "Hail":-6} #how each weather should affect the experienced temp
        stage_effects = {"Morning":-1, "Afternoon":4, "Night":-3} #how each stage of the day should affect the experienced temp

        self.feels_like_temp = self.environment_temp + weather_effects[self.weather] + stage_effects[self.current_stage]

    def find_available_locations(self):
        '''Returns a list of available locations from one location.'''
        routes = list(self.locations[self.current_location].accessible_locations) #each location you index (e.g. Stockholm) is an object, so it has accessible properties
        return routes

    def update_location(self, new_location):
        '''Updates location to the new location.'''
        self.current_location = new_location

    def access_current_location_info(self):
        '''Uses the self.locations dictionary to return a Location instance of the location you are in.'''
        return self.locations[self.current_location]

    def access_current_location_specific(self, specific):
        '''Accesses a specific detail (e.g. direction, distance_to, stages_needed or requirements) of current location.'''
        return getattr(self.access_current_location_info(), specific) #uses get attribute to find the attribute of the current location

    def access_destination_info(self, destination):
        '''Uses the self.locations dictionary, and a location parameter (has to be valid) to return a inner dictionary with info of the destination.'''
        return self.access_current_location_info().accessible_locations[destination]

    def access_destination_specific(self, destination, specific):
        '''Accesses a specific detail (e.g. direction, distance_to, stages_needed or requirements) of a destination. Must be done before updating location to destination.'''
        return self.access_destination_info(destination)[specific]

    def rest(self):
        '''The player rests. Takes one day (3 stages) and food goes down by 1, but health goes up by 3.'''

        # Cutscene - uses environment & time based things to change the message
        self.log(f"You sleep. (Or at least try to.)")
        self.custom_sleep(REAL_TIME_PER_STAGE)

        rest_cutscene_message = self.get_rest_message()
        self.log(rest_cutscene_message)

        self.custom_sleep(3 * REAL_TIME_PER_STAGE)

        # Updating stats - but stats updated depends on the current food level - if you have no food you don't heal as your body has no energy

        if self.player.food_level >= 6:
            health_gain = 3
            food_drain = 1
        elif self.player.food_level >= 3:
            health_gain = 1.5
            food_drain = 1
        elif self.player.food_level > 0:
            health_gain = -1.5
            food_drain = 1
        else:
            health_gain = -2
            food_drain = 0

        
        if health_gain > 0:
            self.player.recover_health(health_gain)
        else:
            self.player.take_damage(abs(health_gain))

        self.player.food_decrease(food_drain)

        self.is_resting = True
        self.advance_stages(3) #which also may randomise weather
        self.is_resting = False
        
        # More cutscene, but uses the updated info.

        # The phrases said in the cutscene when you wake up
        weather_wake_phrases = {
          "Rain": "the dull drumming of freezing rain",
          "Clear": "pale, blinding sunlight across the permafrost",
          "Cloudy": "overcast skies",
          "Snowstorm": "a howling snowstorm blowing snow around",
          "Strong Winds": "violent gale winds whistling",
          "Snow": "silent, heavy snowfall",
          "Hail": "the sharp rattling of hail against the walls",
      }

        phrase = weather_wake_phrases[self.weather] #by here weather should be updated

        self.log(f"You wake up slightly hungry to {phrase}.")

        health_status_message = self.get_health_status_message()

        self.custom_sleep(REAL_TIME_PER_STAGE)

        self.log(f"{health_status_message}")

        self.refresh_screen()

    def get_health_status_message(self):
        '''Depending on current health, return random messages reflecting that health.'''

        health_messages = {

            # 9 - 10 hearts
            "full":["You feel [bold green]very[/bold green] good.", 
                    "Your muscles feel electric and your brain feels sharp.", 
                    "A passerby looks at you, and compliments your looks today."],

            # 6.5 - 8.5 hearts
            "healthy":["You stand up confident, though a gust of wind reminds you that its cold.", 
                       "Your joints feel stiff as you try to move around, but you're holding up fine.", 
                       "Your body groans, but nothing is wrong."],

            # 3.5 - 6 hearts
            "injured":["A needle-like pain shoots through your limbs with every sudden movement.",
                       "Exposed skin starts freezing and stings heavily in the cold.",
                       "You feel [bold yellow]worn down and battered[/bold yellow].\nYou remind yourself to be careful."],

            # 0.5 - 3 hearts
            "critical":["Each breath feels like inhaling broken glass shards.\nYour eyes start hallucinating things.",
                        "A heavy, numb exhaustion drags you back down to the ground.\nYou don't feel refreshed at all.",
                        "You are [bold red]shivering violently[/bold red] and barely clinging to consciousness."]
        }

        health = self.player.health
        
        if health >= 9:
            category = "full"
        elif health >= 6.5:
            category = "healthy"
        elif health >= 3.5:
            category = "injured"
        else:
            category = "critical"

        return choice(health_messages[category]) #returns a random message based on the category

    def get_rest_message(self):
      """Gets a generic, sensory sleep message based on weather or time of day,

      avoiding specific shelter structures or equipment assumptions.
      """

      # Changes based on weather
      weather_sleep_messages = {
          "Snowstorm": [
              (
                  "The roar of the blizzard drowns out all thought. You curl in"
                  " tight, shivering relentlessly as exhaustion takes hold."
              ),
              (
                  "Howling wind drives ice against you from the dark. You shut"
                  " your eyes and brace against the biting cold."
              ),
              (
                  "The whiteout roars around you. Teeth chattering, you force"
                  " yourself to lie still until sleep comes."
              ),
          ],
          "Strong Winds": [
              (
                  "Violent gusts buffet against you without pause. You tuck"
                  " your limbs in close to conserve every ounce of warmth."
              ),
              (
                  "The wind howls violently in your ears as you close your eyes"
                  " against the draft."
              ),
              (
                  "Sharp gales tear through the air. You curl down low,"
                  " waiting for sleep to pull you under."
              ),
          ],
          "Rain": [
              (
                  "Freezing water drips and soaks through to your skin. You"
                  " shut your eyes, trying to ignore the creeping dampness."
              ),
              (
                  "The steady drumming of icy rain echoes in the dark as your"
                  " heavy eyelids finally shut."
              ),
              (
                  "Cold moisture chills you to the bone, but sheer exhaustion"
                  " drags you toward sleep anyway."
              ),
          ],
          "Hail": [
              (
                  "Sharp ice pellets clatter all around you. You protect your"
                  " face and wait out the stinging storm."
              ),
              (
                  "The harsh clatter of falling ice surrounds you in the dark"
                  " as your body finally yields to fatigue."
              ),
          ],
      }

      # Changes based on time of day
      stage_sleep_messages = {
          "Morning": [
              (
                  "Exhaustion hits you early. You shut your eyes against the"
                  " pale morning light and rest."
              ),
              (
                  "The air is bitterly sharp, but heavy fatigue forces you"
                  " down to sleep."
              ),
          ],
          "Afternoon": [
              (
                  "With the day half-spent, fatigue clouds your mind and you"
                  " drift into a deep slumber."
              ),
              (
                  "The dim afternoon light fades into gray as your body finally"
                  " gives out to sleep."
              ),
          ],
          "Night": [
              (
                  "Sub-zero darkness settles in. You hug your knees tight,"
                  " listening only to your own frosted breath."
              ),
              (
                  "The nighttime chill bites viciously. You curl into a ball,"
                  " shivering as sleep pulls you under."
              ),
              (
                  "Darkness brings a brutal freeze. You close your eyes,"
                  " drifting into uneasy rest."
              ),
          ],
      }

      if self.weather in weather_sleep_messages:
        return choice(weather_sleep_messages[self.weather])

      return choice(
          stage_sleep_messages.get(
              self.current_stage, stage_sleep_messages["Night"]
          )
      )

    def update_action_menu_status(self, status):
        '''Updates the action menu status to open or closed.'''
        if status in [True, 'Open']:
            self.action_menu_open = True
        else:
            self.action_menu_open = False

    def calculate_num_visual_rows(self, text):
        '''Calculates, based on the dialogue box width, how many rows a string of text will take up.'''

        # Remove rich colour tags
        clean_text = re.sub(r"\[.*?\]", "", text)

        visual_rows = 0

        splitted_text = clean_text.split("\n") #splits at new lines

        for paragraph in splitted_text:
            if len(paragraph) == 0: #if nothing on the line
                visual_rows += 1
            else:

                # Each row would take up the length / the available width, but since rows have to be integers, you round up
                visual_rows += math.ceil(len(paragraph) / USABLE_WIDTH)

        return visual_rows

    def return_requirements_checked_accessible_locations(self):
        '''Checks all accessible locations you can get to, and calls other functions to check requirements'''

        pass #WIP - but used in travel input (maybe make it accessible_location's list)

    def travel_input(self, locations_list):
        '''Gets the input for where the user needs to go (either an index or a name). Accounts for error messages and printing layouts. Takes accessible locations list as input.'''

        all_locations_names = list(self.locations.keys())
        lowercase_all_locations_names = [item.lower() for item in all_locations_names]
        #locations_list = return requirements checked accessible locations ?

        accessible_locations_list_lowercase = [location.lower() for location in locations_list]

        error_message = ""

        #loop ends with return statements instead
        while True: 
            
            #each iteration of the loop REDRAWS the interface, to prevent error messages / prompt messages looking weird
            self.refresh_screen()

            # prompting the user below the dialogue box instead of in it

            
            #listing out options to user 
            for index, location in enumerate(locations_list): #uses available location list
                print(f"Location #{index+1}: {location}") #prints like regular

            print("Out of the locations, where would you like to go?")



            if error_message != "": #if there is an error message
                print(f"\n[bold red]{error_message}[/bold red]") #prints error message in red

            # gets user input
            desired_location = input("Enter the location name, or location number.").strip()

            '''Case #1 - If the user inputted a number.'''
            try:
                # gets the index you entered and converts to 0 indexing
                location_index = int(desired_location) - 1
                
                if 0 <= location_index <= len(locations_list) - 1: #valid location - within bounds & uses 0 indexing
                    return locations_list[location_index] #exits loop
                else: #invalid - give an error message
                    error_message = f"Number '{desired_location}' is out of range."
                    continue #go through loop again

            # if not (meaning an error), then move on
            except ValueError:
                pass

            '''Case #2 - If the user entered a string instead '''

            lowercase_input = desired_location.lower()

            if lowercase_input in accessible_locations_list_lowercase: #if the location selected is valid (part of the accessible locations of the location)
                index_location = accessible_locations_list_lowercase.index(lowercase_input) #finds index of the location
                return locations_list[index_location] #uses the index to return the location name

            elif lowercase_input in lowercase_all_locations_names: #if the user wants to go to a valid location on the map, but not accessible from that location
                error_message = f"Uhh... You can't go to '{desired_location}' from here."

            else:
                error_message = f"'{desired_location}' is not a place on this map."        

    def travel(self):
        '''Allow player to select from menu options (based on the current location's available nodes) to travel somewhere. Consumes food based on distance. Updates all variables.'''

        #all locations names

        # all_locations_names = list(self.locations.keys())
        # lowercase_all_locations_names = [item.lower() for item in all_locations_names]

        #find available locations
        
        current_location_info = self.access_current_location_info() #This accesses a location instance - meaning attributes of that location can be accessed
        locations_list = list(current_location_info.accessible_locations.keys()) #finds locations accessible from the current location - keys() returns a list of keys in that dictionary

        origin_location = self.current_location

        desired_location = self.travel_input(locations_list)

        self.log(f"You chose to go to {desired_location}!")

        #get direction and distance and display to user
        direction = self.access_destination_specific(desired_location, "direction_to")
        distance = self.access_destination_specific(desired_location, "distance_to")

        self.log(f"You are heading {direction} for {distance} km.")

        # based on the amount of stages needed, wait a proportional amount of time and tell the user you reached the destination
        stages_needed = self.access_destination_specific(desired_location, "stages_needed")
        days_needed = round(stages_needed / 3, 2) #round to 2dp

        time_wait = stages_needed * REAL_TIME_PER_STAGE 
        self.custom_sleep(time_wait)

        # make it say days if plural, day if not plural
        plural = 's' if days_needed != 1 else ''
        
        self.log(f"You arrived in {desired_location} after {days_needed} day{plural} of travel from {origin_location}.")
        
        #update their food bar (every stage needed = 1 bar of food consumed)
        
        self.player.food_decrease(stages_needed)

        # update the day counter / stages
        self.is_travelling = True
        self.advance_stages(stages_needed)
        self.is_travelling = False

        # update their location
        self.update_location(desired_location)

        # print(f"DEBUG: Old location was {origin_location}")
        # print(f"DEBUG: New location is {self.current_location}")
        # print(f"DEBUG: left_camp_before is now {self.left_camp_before}")
        # input("Press Enter to continue...")

        #re-set current location info since we have changed location
        current_location_info = self.locations[self.current_location]

        # update temperature and re-randomise weather (randomise maybe 50% of the time)
        self.environment_temp = self.access_current_location_specific("temp") #Location class attribute - not Game class attribute
        self.randomise_weather()
        self.update_feels_like_temp()

        if origin_location == "Permafrost Camp": #to activate xavier's cutscene - update once player has left the spawn
            self.left_camp_before = True
        self.check_quest_triggers() # check if you need to end or start any quests at your new location

    def display_top_info(self):
        '''Within the interface, displays specifically the top row - including the day counter, weather, stage counter, temperature and location.'''
        top_row = Columns([Panel(f"Day {self.day} | {self.current_stage} | {self.formatted_date}", border_style=TOP_INFO_BORDERS, expand=False),
                           Panel(f"Currently at {self.current_location}", border_style=TOP_INFO_BORDERS, expand=False),
                           Panel(f"{self.get_weather_symbol()} {self.temperature_convert(self.feels_like_temp, self.settings["temp_unit"]["Status"])}", width=14, border_style=TOP_INFO_BORDERS, expand=False)]) 
        
        #one row, accounting for the top and bottom
        location_description_banner = Panel.fit(f"[i dim]{self.locations[self.current_location].description}[/i dim]", height=3, border_style=TOP_INFO_BORDERS)

        print(top_row)

        print(location_description_banner)

    def display_node_map_visual(self):
        '''Displays a node map where you can physically see the locations (that you can currently access at your node) of each of the nodes on a map.'''

        # Note - map is slightly abstracted, and does not have support for NE, SW or NNE etc... but does display the exact direction inside the node itself

        current_location = self.current_location

        #lowercase version - note i dnidnt use emojis due to a weird visual bug with the boxes
        display_arrows = {
            "north": "[cyan]▲ N[/cyan]",
            "northeast": "[cyan]▲NE[/cyan]",
            "northwest": "[cyan]▲NW[/cyan]",
            "north-northwest": "[cyan]▲NNW[/cyan]",
            "north-northeast": "[cyan]▲NNE[/cyan]",

            "south": "[cyan]▼ S[/cyan]",
            "southeast": "[cyan]▼SE[/cyan]",
            "southwest": "[cyan]▼SW[/cyan]",
            "south-southeast": "[cyan]▼SSE[/cyan]",
            "south-southwest": "[cyan]▼SSW[/cyan]",

            "east": "[cyan]► E[/cyan]",
            "east-southeast": "[cyan]►ESE[/cyan]",
            "east-northeast": "[cyan]►ENE[/cyan]",

            "west": "[cyan]◄ W[/cyan]",
            "west-northwest": "[cyan]◄WNW[/cyan]",
            "west-southwest": "[cyan]◄WSW[/cyan]"
        }

        current_accessible_locations = self.locations[current_location].accessible_locations

        north_list = []
        south_list = []
        east_list = []
        west_list = []

        for location_name, location_data in current_accessible_locations.items(): #returns dictionary items for the location you want to get to
            direction_to_location = location_data["direction_to"].lower().strip() #get the direction you need to go to get to that location

            arrow_display = display_arrows.get(direction_to_location, "No direction found") #finds the arrow display for that 

            # adds a panel (a visual box) for each specific node and used to display later
            display_text = f"[bold white]{location_name}[/bold white]\n[cyan]{arrow_display} ({location_data['distance_to']} km)[/cyan]"
            display_panel = Panel(display_text, expand=False, border_style="cyan") #30 widht prevents weird box widths

            if "north" in direction_to_location: #if direction_to includes n (north)
                north_list.append(display_panel)
            elif "south" in direction_to_location: #if direction_to includes s (south)
                south_list.append(display_panel)

            elif "east" in direction_to_location: #east and west have only one option
                east_list.append(display_panel)
            elif "west" in direction_to_location:
                west_list.append(display_panel)

            else:
                # if direction isn't valid somehow, adds to north list
                center_list = north_list
                center_list.append(display_panel)          

        current_location_panel = Panel(
            f"[bold yellow]YOU ARE HERE[/bold yellow]\n[bold white]{current_location}[/bold white]\n[dim]Distance left: {self.distance_left} km[/dim]",
            expand=False,
            border_style="bold yellow"
        )

        # map parts is like a list of the rows you want to display from top to bottom
        # adds the top things like the title, then the top rows, and middle and finally bottom nodes
        map_parts = []

        map_parts.append(Align.center("[bold red]Map of accessible locations[/bold red]"))
        map_parts.append("")
        
        # finally, after adding the panels (visuals) into the lists, display all of them

        if north_list:
            for panel in north_list:
                map_parts.append(Align.center(panel))
                map_parts.append(Align.center("[cyan]▲[/cyan]")) #arrow pointing north

        middle_row = [] #for mdidle of screen

        if west_list:
            middle_row.append(Group(*west_list)) #special syntax used -- unpack arguments (basically pass in the list items instead of the list itself)
        
        middle_row.append(current_location_panel) #display the current location visual in the middle of the screen 
        
        if east_list:
            middle_row.append(Group(*east_list)) #unpack arguments (basically pass in the list items instead of the list itself)

        map_parts.append(Align.center(Columns(middle_row, padding=4)))

        if south_list:
            for panel in south_list:
                map_parts.append(Align.center("[cyan]▼[/cyan]")) #arrow pointing south
                map_parts.append(Align.center(panel))

        self.clear_screen()
        print(Panel(Group(*map_parts), border_style=TOP_INFO_BORDERS, title="[dim]Map[/dim]", title_align="left"))
        
        print("\n[dim]Press Enter to return to action menu [/dim]")
        input()
        # when you press enter, it leaves the subroutine and goes back to the menu

    def display_sidebar(self):
        '''Within the interface, displays the sidebar - which includes the "buttons" to open the inventory, clothing menu and open the actions menu.'''

        if self.action_menu_open == False: #helps user open action menu if not open
            additional_text = "[dim]\nPress Enter to Open[/dim]"
        else:
            additional_text = ""

        if self.current_quest != None:
            quest_display = self.current_quest.get_quest_display()

            progress_display = self.current_quest.get_progress_display()
        else:
            quest_display = "Quest Status:\n No current quest."
            progress_display = "----------------------"

        #set fixed width to make sure it looks good
        sidebar_buttons = [Panel(f"{quest_display}", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False), 
                           Panel(f"{progress_display}", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False), 
                           Panel(f"🔧 Actions Menu      {additional_text}", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False)]

        #prints all of them at once
        print(Align.right(Group(*sidebar_buttons)))

    def get_health_display(self):
        '''Gets the hotbar's health bar display and returns it. Health can either be at 1 or 0.5 increments.'''
        health = self.player.health

        #the variables are the AMOUNT of each heart (total = 10)
        full_hearts = int(health // 1)
        half_hearts = 1 if health % 1 == 0.5 else 0 #if you are on a decimal half heart health, you have 1 half heart, otherwise u have 0

        empty_hearts = int(MAX_HEALTH - full_hearts - half_hearts)

        hearts_string = empty_hearts * EMPTY_HEART_SYMBOL + half_hearts * HALF_HEART_SYMBOL + full_hearts * FULL_HEART_SYMBOL

        return hearts_string

    def get_food_bar_display(self):
        '''Gets the hotbar's food display and returns it. In 0.5 or 1 increments.'''

        food = self.player.food_level

        full_food = int(food // 1)
        half_food = 1 if food % 1 == 0.5 else 0

        empty_food = int(MAX_FOOD - full_food - half_food)

        food_string = empty_food * EMPTY_FOOD_SYMBOL + half_food * HALF_FOOD_SYMBOL + full_food * FULL_FOOD_SYMBOL

        return food_string

    def get_body_temp_display(self):
        '''Formats the body temperature thing and returns it so it can be displayed on the hotbar.'''
        temp = self.player.body_temp

        if temp >= 36.5:
            colour = "bold green"
            icon = "🌡️ "
        elif temp >= 35.0:
            colour = "bold yellow"
            icon = "🥶"
        elif temp >= 33.0:
            colour = "bold cyan"
            icon = "🧊"
        else:
            colour = "bold magenta"
            icon = "💀"

        return f"[{colour}]{icon} {self.temperature_convert(temp, self.settings["temp_unit"]["Status"])}[/{colour}]" #adds the right icons and rounds temp to 1dp

    def display_hotbar(self):
        '''Within the interface, displays the hotbar (bottom) - which includes the health, food levels, body temperature and symbol.'''

        hearts = self.get_health_display()
        food = self.get_food_bar_display()
        body_temp = self.get_body_temp_display()


        print(f"{hearts}{HOTBAR_SPACING * ' '}{food}{HOTBAR_SPACING * ' '}{body_temp}")

    def display_dialogue_box(self):
        '''Displays the dialogue box within the interface at the bottom, with the 5 most recent messages (from most recent at the bottom to least at the top.)'''

        # reverses the past dialogue (to make it go from recent at lower indexes)
        lines = self.past_dialogue[-DIALOGUE_TEXT_ROWS:]

        styled_lines = []

        #style the most recent like bold white and everything else gray
        for index, line in enumerate(lines):
            if index == len(lines) - 1: #if most recent (at the bottom)
                styled_lines.append(f"[bold]{line}[/bold]")
            else:
                styled_lines.append(f"[dim]{line}[/dim]")

        #joins a string and in between them adding newlines
        dialogue_string = "\n".join(styled_lines)

        dialogue_box = Panel(f"{dialogue_string}", width=DIALOGUE_WIDTH, height=DIALOGUE_TEXT_ROWS + 2) # +2 for borders

        print(dialogue_box)

    def log(self, text, specific_colour=None, force_typewriter=False):
        '''Logs text into the upcoming record logs to be displayed later.
        If typewriter mode is on, it uses self.custom_sleep() and displays the messages character by character by refreshing the screen each time - like how a video works.'''

        # For any mode just log into the records as normal

        typewriter = self.settings["typewriter"]["Status"] #grabs from settings instead.

        delay = float(self.settings["typewriter_speed"]["Status"]) #grabs from settings
        
        if specific_colour == None:
            self.record_past_dialogue(text)
        else:
            self.record_past_dialogue(f"[{specific_colour}]{text}[/{specific_colour}]")

        if not typewriter and not force_typewriter or self.typewriter_override: #overrides typewriter
            return None # ends the function, since if the mode is off we dont need the typewriter

        #Typewriter code

        self.past_dialogue[-1] = "" # makes the message typed empty, so it can start printing char by char
        self.refresh_screen()

        has_markup = "[" in text and "]" in text #check if text has markup codes

        for character in text:
            if specific_colour is not None and not has_markup:
                self.past_dialogue[-1] += f"[{specific_colour}]{character}[/{specific_colour}]"
            else:
                # if it already contains markup tags or has no specific colour, type raw characters cleanly
                self.past_dialogue[-1] += character
            #adds one character, then refreshes the screen after a delay
            self.custom_sleep(delay)
            self.refresh_screen()

    def temperature_convert(self, temp_c, unit):
        '''Converts temperatures from Celcius.'''

        if "F" in unit:
            temp_f = temp_c * 9/5 + 32
            return f"{temp_f:.1f}°F"
        elif "K" in unit:
            temp_k = temp_c + 273.15
            return f"{temp_k:.1f}°K"
        else:
            return f"{temp_c:.1f}°C"

    def log_chunk_to_single_line(self):
        '''
        NOTE: Kept just in case, but AVOID using since if you need to do a chunk of text
        you should just do it below the dialogue box using normal print() statements.
        
        Logs a chunk of text as a single log within the records, maintaining the original order. Uses the self.current message block.
        If nothing in current message, do nothing.
        Single chunk of message still should not exceed the DIALOGUE_TEXT_ROWS.
        
        This will print the text instantly without the typewriter effect, unless specified.
        
        '''
        if self.current_message_block == []:
            return None

        self.log("\n".join(self.current_message_block))
        self.current_message_block = [] #clears current message block

    def record_past_dialogue(self, text):
        '''Stores a new dialogue in the records. Only keeps the last X (controlled by DIALOGUE_TEXT_ROWS) dialogues in the dialogue box. The higher index the message the more recent.'''
        
        # adds the text to the stored records
        self.past_dialogue.append(text)

        # calculate total amount of lines that our record (self.past_dialogue) currently uses
        total_lines = 0
        for log in self.past_dialogue:
            total_lines += self.calculate_num_visual_rows(log)

        while total_lines > DIALOGUE_TEXT_ROWS and len(self.past_dialogue) != 0: #loop while our number of lines exceeds the limit and our log isn't empty
            removed_chunk = self.past_dialogue.pop(0)
            total_lines -= self.calculate_num_visual_rows(removed_chunk) #same counting system as before, if you pop the chunk from the list, remove its length from total lines

    def refresh_screen(self):
        '''Refreshes the screen and updates the interface to represent changes immediately - but doesn't update the turn.
        Should be placed after every action subroutine (e.g. opening inventory, using item, resting, travelling etc.)'''
        self.clear_screen()
        self.display_interface()

    def display_interface(self, exclusive=False):
        '''Displays the main game's interface - the top info, sidebar, hotbar, dialogue box.'''
        self.display_top_info()
        self.display_sidebar()
        self.display_hotbar()
        if not exclusive: # can toggle off printing the display dialogue box
            self.display_dialogue_box()
        
    def open_inventory_menu(self):
        '''Opens the inventory menu.'''

        slot_names = ["Head", "Torso", "Legs", "Feet"]

        error_message = ""

        while True:
            self.refresh_screen() #for each input you first refresh the screen

            if error_message != "": #if there was an error, display it
                print(f"\n[bold red]{error_message}[/bold red]\n") #prints error message in red

            # This section displays warmth and the current clothing

            print(f"[underline][bold red]Current clothing and inventory[/bold red][/underline]")
            
            current_clothing = self.player.clothing

            total_warmth = 0

            for slot_name, clothing_item in zip(slot_names, current_clothing):

                # Display

                if clothing_item is not None:
                    clothing_item_display = clothing_item.return_coloured_name(clothing_item)

                    # Warmth - add clothing warmth to total if there is an item
                    total_warmth += clothing_item.get_stat("Warmth", 0)

                else: # if there is no clothing item in a slot
                    clothing_item_display = "[dim]Empty[/dim]"

                print(f"   {slot_name}: {clothing_item_display}")

            print(f"[red]Total Warmth:[/red] {total_warmth*100:.1f}%")

            # Backpack

            backpack_items_quantity = len(self.player.backpack)

            backpack_items = self.player.backpack

            # Displays used slots
            print(f"\n[underline]Backpack: {backpack_items_quantity}/{BACKPACK_LIMIT} slots [red]used[/red].[/underline]\n")

            for index, backpack_item in enumerate(backpack_items):

                display_number = index + 1

                backpack_item_display = backpack_item.return_coloured_name(backpack_item)

                durability_display = backpack_item.get_durability_display()

                print(f"[{display_number}] - {backpack_item_display} {durability_display}")

            # Get the maximum display from the first loop

            maximum_index = len(self.player.backpack)

            # Satchel

            satchel_items_quantity = len(self.player.satchel)

            satchel_items = self.player.satchel

            print(f"\n[underline]Satchel: {satchel_items_quantity}/{SATCHEL_LIMIT} slots [red]used[/red].[/underline]\n")

            for index, satchel_item in enumerate(satchel_items):

                display_number = index + maximum_index + 1 #adds maximum index to continue counting

                satchel_item_display = satchel_item.return_coloured_name(satchel_item)

                durability_display = satchel_item.get_durability_display()

                print(f"[{display_number}] - {satchel_item_display} {durability_display}")



            # Selection of items

            # temporarily combine the items into one big inventory so that choosing an item is easier
            all_inventory_items = self.player.backpack + self.player.satchel

            desired_index = input("\nEnter the number of the item you want to select (or enter E to exit).\n").upper()

            if desired_index.upper() == 'E':
                self.refresh_screen() #refresh to remove everything
                return None #exit loop and menu

            try: #check if it is an integer
                desired_index = int(desired_index)

            except:
                error_message = f"That is not a number."
                continue #go to next loop

            if 1 <= desired_index <= len(all_inventory_items): #this uses 1 based index since it is a UI
                desired_index -= 1 #convert to 0-indexing
                desired_item = all_inventory_items[desired_index]
                break #exit loop only

        # At this point the item should be selected along with the 0-indexing index.

        #remove the previous menu and open a new one

        error_message = ""

        while True: #another selection menu
            self.refresh_screen()

            if error_message != "": #if there was an error, display it
                print(f"\n[bold red]{error_message}[/bold red]") #prints error message in red
            
            if desired_item.item_type == "Food":
                print(f"[1] Eat / Consume")
                print(f"[2] Discard")
                print(f"[E] Exit item menu")

                option = input(f"Select an option in [].\n").strip()

                if option == "1":
                    health_increase = math.floor(desired_item.get_stat("Food", 0) * FOOD_TO_HEALTH_CONVERSION)
                    self.player.food_increase(desired_item.get_stat("Food", 0))

                    self.player.recover_health(health_increase) #recovers health based on conversion

                    backpack_index = self.player.backpack.index(desired_item)

                    if desired_item.quantity_remaining == 1:
                        self.player.backpack.remove(desired_item) #remove from inventory if only have 1
                        self.refresh_screen() #since item is gone
                        break

                    else: #decrease qty by 1
                        self.player.backpack[backpack_index].quantity_remaining -= 1
                        break

                elif option == "2":
                    print(f"Your hand wants to throw away the food. Your mind stops you. Your hand stuns, and you stop.")
                    self.custom_sleep(2.0)
                    break #get to other menu

                elif option.upper() == "E":
                    break #exit loop to head to other menu

                else:
                    error_message = "Sorry, that is not an option."
                    continue #next loop

            elif "Clothing" in desired_item.item_type: # IF any type of clothing

                print(f"[1] Equip")
                print(f"[E] Exit item menu")

                option = input(f"Select an option in [].\n").strip()

                if option == "1":
                    backpack_index = self.player.backpack.index(desired_item)

                    # map the clothing to correct spot
                    slot_map = {
                        "Clothing Head": 0,
                        "Clothing Top": 1,
                        "Clothing Bottom": 2,
                        "Clothing Shoes": 3
                    }

                    clothing_slot_index = slot_map.get(desired_item.item_type, 1)

                    if self.player.clothing[clothing_slot_index] == None: #if empty slot, just equip item, remove from inventory
                        self.player.clothing[clothing_slot_index] = desired_item

                        if desired_item.quantity_remaining == 1:
                            self.player.backpack.remove(desired_item) #remove if only one
                            self.refresh_screen() #since item is gone
                            break

                        else: #decrease quantity by 1
                            self.player.backpack[backpack_index].quantity_remaining -= 1
                            break

                    else: #otherwise add the item back to inventory after removing it, and remove new item from inventory and equip
                        equipped_clothing = self.player.clothing[clothing_slot_index]
                        self.add_item_to_inventory(equipped_clothing, "backpack")

                        # swaps it for the desired clothing item
                        self.player.clothing[clothing_slot_index] = desired_item

                        #remove the clothing item
                        if desired_item.quantity_remaining == 1:
                            self.player.backpack.remove(desired_item) #remove if only one
                            self.refresh_screen() #since item is gone
                            break

                        else: #decrease quantity by 1
                            self.player.backpack[backpack_index].quantity_remaining -= 1
                            break

                elif option.upper() == "E":
                    break #exit loop to head to other menu

                else:
                    error_message = "Sorry, that is not an option."
                    continue #next loop

            

            elif desired_item.is_quest_item == True: #is a quest item

                print(f"[1] Use item")
                print(f"[2] Discard item")
                print(f"[E] Exit item menu")

                option = input(f"Select an option in [].\n").strip()

                if option == "1":
                    self.quest_items_routing(desired_item) #a function that takes a quest item and routes it to generate each item's custom menu


                    #when routing finished, just exit the inventory
                    self.refresh_screen()
                    return None #exit

                elif option == "2":
                    error_message = "[bold red]Your survival instincts prevent you from discarding vital quest items."
                    continue

                elif option.upper() == "E":
                    break

                else:
                    error_message = "Sorry, that is not an option."
                    continue #next loop

            elif desired_item.item_type in ["Tool", "Utility"]:

                print(f"[1] Use item")
                print(f"[2] Discard 1 of the item")
                print(f"[E] Exit item menu")

                option = input(f"Select an option in [].\n").strip()

                if option == "1":
                    print(f"Ooh... Seems like you can't use this item until important cutscenes. Unfortunate.")
                    break # goes to more options

                elif option == "2":
                    #remove the item
                    if desired_item.quantity_remaining == 1:
                        self.player.backpack.remove(desired_item) #remove if only one
                        self.refresh_screen() #since item is gone
                        break

                    else: #decrease quantity by 1
                        desired_item.quantity_remaining -= 1
                        break
                
                elif option.upper() == "E":
                    break

                else:
                    error_message = "Sorry, that is not an option."
                    continue #next loop

        #choose to exit at the end
        print(f"[V] View other items")
        print(f"[E] Exit inventory")

        print(f"[bold green]What would you like to do next?[/bold green]")
        new_option = input()
        
        if new_option.upper() == "V":
            return self.open_inventory_menu()

        elif new_option.upper() == "E":
            self.refresh_screen() #refresh to remove menu
            return None #exit

        else:
            print(f"Invalid option - automatically exiting...")
            self.custom_sleep(0.8)
            self.refresh_screen()
            return None #exit

    def view_detailed_stats(self):
        '''Opens a menu of detailed stats.'''
        pass #WIP

    def add_item_to_inventory(self, item, inventory="backpack"):
        '''Adds an item to a specific inventory. If inventory already contains that item, add 1 to the quantity remaining.'''

        if inventory == "backpack": #if it is a backpack, add it to the backpack IF there is no other copy, otherwise increment the quantity.
            if item not in self.player.backpack:
                self.player.backpack.append(item)
            else:
                self.player.backpack[self.player.backpack.index(item)].quantity_remaining += 1
        elif inventory == "satchel" or item.is_quest_item:
            if item not in self.player.satchel:
                self.player.satchel.append(item)
            else:
                self.player.satchel[self.player.satchel.index(item)].quantity_remaining += 1
        else:
            raise ValueError("No inventory like this available.")

    def add_items_to_inventory(self, item, quantity, inventory="backpack"):
        '''Adds many items to one specified inventory.'''
        for _ in range(quantity):
            self.add_item_to_inventory(item, inventory)

    def quest_items_routing(self, quest_item):
        '''For each specific quest item, opens a different quest item menu.'''
        pass

    def get_action(self):
        '''Get the action from the player. (Travel, open inventory, view advanced stats etc). Returns a string.'''

        #Opens action menu when Enter pressed
        print("\n[bold red]Press Enter to open Action Menu...[/bold red]")
        input()

        self.update_action_menu_status("Open")

        # Maps numerical values and text to actions so the player can type a number instead of the whole action thing
        valid_actions = {

            "1":"travel",
            "travel":"travel", #may seem redundant but maps the text to the same action

            "2":"inventory",
            "inventory":"inventory",

            "3":"rest",
            "rest":"rest",

            "4":"stats",
            "stats":"stats",

            "5":"settings",
            "settings":"settings",

            "6":"map",
            "map":"map",

            "7":"tutorial",
            "tutorial":"tutorial",

            "8":"close",
            "close":"close"

        }

        # Similar logic to the travel_input(), uses an indefinite loop but ends using return statements

        error_message = ""

        while True:

            self.refresh_screen()

            # Shows the user the options
            print("\n[bold yellow]What would you like to do?[/bold yellow]")
            print("  [1] Travel to a new location")
            print("  [2] Open Inventory & Gear")
            print("  [3] Rest / Wait")
            print("  [4] View Detailed Stats")
            print("  [5] Open Settings")
            print("  [6] Open Node Map")
            print("  [7] Game Mechanics Explanation")
            print("  [8] Close Action Menu")

            if error_message != "": #if there was an error in the last loop:
                print(f"\n[bold red]{error_message}[/bold red]")

            desired_action = input("\nEnter a choice or number.").strip().lower()

            if desired_action in valid_actions.keys(): #if the action is in the valid actions dictionary
                return valid_actions[desired_action] #return the requested action

            #otherwise give the error message

            error_message = f"'{desired_action}' is not a valid action. Choose 1-4 or type the command name."

    def do_action(self, action):
        '''Performs the action by calling smaller subroutines'''

        if action == "travel":
            self.travel()

        elif action == "rest":
            self.rest()

        elif action == "inventory":
            self.open_inventory_menu()

        elif action == "stats":
            self.view_detailed_stats()

        elif action == "settings":
            self.open_settings_menu()

        elif action == "map":
            self.display_node_map_visual()

        elif action == "tutorial":
            self.open_tutorial_menu()

        elif action == "close":
            self.update_action_menu_status("Closed")
            self.refresh_screen()

    def custom_sleep(self, duration):
        '''Sleeps IF self.typewriter_override is off.'''
        if not self.typewriter_override:
            sleep(duration)

    def open_tutorial_menu(self):
        '''Opens a tutorial menu with "pages" to scroll past to explain the game without using cutscenes (more directly). Currently does key mechanics like:
        Body temperature
        Movement
        Food
        Inventory
        '''

        # Sets up pages and their content (each tuple is one page)
        pages = [
            (
                "[bold cyan]Movement[/bold cyan]", 
                "• In Expedition 13, you can [b red]only[/b red] move between [cyan]nodes (locations)[/cyan]. You cannot move freely.",
                "• Travel takes a certain amount of [yellow]stages[/yellow] in the day ([yellow]time[/yellow]), as well as consuming your [brown]food bar[/brown] and exposing you to the outside cold - determined differently depending on factors.",
                "[i](Every 25 km or less of travel takes 1 more stage and consumes 1 more food bar.)[/i]",
                "• You can open the node map using [bold]6[/bold] in the action menu in order to check the locations you can get to from your current location."
            ),
            (
                "[bold cyan]Body Temperature & Shelter[/bold cyan]",
                "• Travelling exposes you to the outside environment temperature, which is influenced by the randomised [cyan]weather[/cyan], the [yellow]time of day[/yellow] and the location's [i]hardcoded[/i] average temperature.",
                "[i]For example, if a location averages -10°C normally, but it is nighttime and there is a snowstorm, then the temperature outside becomes -17°C.[/i]",

                "• Different locations have different [magenta]shelter ratings[/magenta], ranging from [red]No Shelter[/red] to [green]Great Shelter[/green].",
                "• If you have [red]no shelter[/red] (like travelling, or staying at an exposed location), your body temperature will try to match the current environment temperature each stage that passes [i]using Newton's law of Cooling[/i].",
                "• Otherwise, [b]any[/b] type of shelter (even poor shelters) will prevent your body temperature from dropping, but will cap out or stabilise your body temperature at a fixed temperature.",
                "[i]For example, if you are at a Poor Shelter, your body temperature will decrease or increase and stabilise at 31.5°C, [b red]regardless[/b red] of the outside temperature.[/i]",

                "• Being too [cyan]cold[/cyan] leads to [bold red]hypothermia[/bold red], and depending on the severity, you can drain food faster while shivering, or take damage due to frostbite (negative effects each stage unless temperature is increased).",
                "• Equipping clothing into their slots increases the [pink1]warmth stat[/pink1], which slows down how fast your temperature drops while not in a shelter. It is [green]additive[/green] across clothing."
            ),
            (
                "[bold cyan]Food and Health[/bold cyan]",
                "• You have a maximum of [bold red]10 health[/bold red] and [bold brown]food bars[/bold brown].",
                "• As you travel, your food bar depletes according to the distance and stages it would need to complete the journey.",
                "[i]Note: specifics of food noted in the travel section[/i]",

                "• Whenever your food bar is completely empty (meaning your body ran out of energy) and an action or anything requires food, it digs into your [bold green]health bar[/bold green] instead.",
                "• [yellow]Resting[/yellow] is an action you can do that advances 1 day whilst consuming 1 food bar and [green]healing[/green] for 3 hearts (maximum)...",
                "[i]...though the hearts healed depend on how much food you have to repair muscles, and may even drain your health if you sleep while starving.[/i]",

                "• When you consume food, it replenishes your food bar based on the type of food, but it also [green]heals health[/green] equal to the food value divided by 2 (then rounded down)."
            ),
            (
                "[bold cyan]Inventory[/bold cyan]",
                "• Items collected are automatically sorted into two inventories: the [yellow]backpack[/yellow], and [magenta]quest satchel[/magenta].",
                "• Whenever an important [magenta]quest item[/magenta] (needed for progression) is obtained, it automatically sorts into the quest satchel, which prevents the item from being dropped or destroyed (stops softlocking).",
                "• Otherwise, survival items like spare clothing, food and other tools are put into an [yellow]8-slot backpack[/yellow], storing your other items and are able to be discarded.",
                "• Most items cannot be directly [red]used[/red] in the inventory. Instead, they are used contextually within [cyan]actions or cutscenes[/cyan]."
            ),
            (
                "[bold cyan]Locations and Cutscenes[/bold cyan]",
                "• Most locations contain [bold yellow]cutscenes[/bold yellow], which activate immediately when you arrive there.",
                "• [orange]NPCs[/orange] live at certain locations and offer you quests, which in exchange, provide [magenta]special items[/magenta] which might be useful later.",
                "• Accessing / getting to certain locations has [cyan]requirements[/cyan], like item requirements, body temperature or other constraints."
            )
        ]

        # index
        current_page = 0

        total_pages_index = len(pages) - 1

        error_message = ""

        while True:
            self.refresh_screen()

            if error_message != "":
                print(f"[bold red]{error_message}[/bold red]\n")

            title, *explanation = pages[current_page] #1st line is the title, the rest the explanation (*explanation makes it a list of things inside instead of one big thing)

            print(title, end="\n\n") #2 lines then bulletpoints

            for line in explanation:
                print(line, end="\n\n") #2 line breaks

            print(f"\n[green]Currently on page {current_page + 1} out of {total_pages_index + 1}[/green] \n[yellow]Choose to go next page (N), exit (E) or go to the previous page (P). [/yellow]")

            choice = input().upper().strip()

            if choice == "E":
                break #exit while loop and therefore exit the subroutine

            elif choice == "N":
                if current_page != total_pages_index:
                    current_page += 1
                # only go next page if the index works
                
            elif choice == "P":
                if current_page != 0:
                    current_page -= 1

            else:
                error_message = "Not a valid option."

    '''Cutscenes Setup'''

    def singular_action_choice(self, choice_display):
        '''Makes the user type the singular action choice before moving on.'''

        error_message = ""

        while True:
            self.refresh_screen()

            if error_message != "": #if there is an error message
                print(f"\n[bold red]{error_message}[/bold red]\n") #prints error message in red
            print(f"{choice_display}")

            self.cutscene_cursor_show()
            option = input()
            self.cutscene_cursor_hide() 

            if option == "1": # make sure to standaridise the option as 1 if there is only 1 action to be done
                return None #exit, as valid

            else:
                error_message = "Not an option available."

    def multi_action_choice(self, choices):
        '''Displays more than 1 choice and ensures a valid choice selection.'''

        error_message = ""
        valid_options = [str(i+1) for i in range(len(choices))] #a list of valid numbers to pick

        while True:
            self.refresh_screen()

            if error_message != "":
                print(f"\n[bold red]{error_message}[/bold red]\n")

            for choice in choices:
                print(choice) #display all choices

            self.cutscene_cursor_show()
            option = input("\nEnter choice: ").strip()
            self.cutscene_cursor_hide()

            if option in valid_options:
                return option #exit loop and return option

            else:
                error_message = f"Invalid option. Please choose an option from 1 to {len(choices)}"

    def log_script(self, script):
        '''Used for cutscenes. Passing in a list, the function will log from back to front (from max index to index 0.) 
        Uses a [separator] notation to pause and indicate a new paragraph.
        Uses a [pause] notation to make the next line an input.
        Uses both [choice] and [/choice] notation to indicate starting an ending choices.
        
        Both [pause] and [choice] create new lines after, so no need to make a SEPARATOR after that.'''

        # if notation is incorrect it won't run

        # used for single and multi action choices
        pause_next_line = False
        collecting_choices_from_script = False
        current_choices = []
        chosen_option = None

        for line in script:

            # detect when you start gathering choices using [choice]
            if line.strip().lower() == "[choice]":
                collecting_choices_from_script = True
                current_choices = [] # reset current choices
                continue # skip printing "[choice]" literally to stop CRASHING
            
            # gathers the option displays for between [choice] and [/choice]
            if collecting_choices_from_script:
                if line.strip().lower() == "[/choice]": #ending option collecting
                    collecting_choices_from_script = False

                    chosen_option = self.multi_action_choice(current_choices)

                    selected_option = current_choices[int(chosen_option) - 1] #chosen option is the 1 based index

                    self.log(f"{selected_option}\n[bold green]Action Selected[/bold green]\n") 
                    continue #prevent 

                else:
                    current_choices.append(line) #adds the line to current choices, but skips printing the line to the dialogue box
                    continue   

            # detect when you start gathering choices using [choice]
            if line.strip().lower() == "[choice]":
                collecting_choices_from_script = True
                current_choices = [] #reset current choices
                continue #skip printing "[choice]" literally

            # detects the other notations, or prints the text as normal
            if line.strip().lower() == "[separator]":
                self.log("")
                self.custom_sleep(0.5)

            # If a pause notation is used, it will signal that the next line becomes an input line, that continues the script
            elif line.strip().lower() == "[pause]":
                pause_next_line = True
                continue

            elif pause_next_line:
                pause_next_line = False
                
                choice_display = line
                self.singular_action_choice(choice_display)
                self.log(f"\n{choice_display}\n[bold green]Action Selected[/bold green]\n", force_typewriter=True)

            else:    
                self.log(line, force_typewriter=True)
                self.custom_sleep(0.1)

    def cutscene_start_setup(self):
        '''Sets up everything correctly at the start of a cutscene.'''
        self.custom_sleep(1) #to not make previous text instantly go away

        self.past_dialogue = [] #empty out previous dialogue

        self.cutscene_cursor_hide()

        self.refresh_screen() #refresh the screen

    def add_slate_log(self, title, bullet_1, bullet_2):
        '''Logs key information inside the slate with a title and two bulletpoints.'''

        title = self.formatted_date + " " + title

        self.slate_entries.append((title, bullet_1, bullet_2))

        self.log(f"\n[bold pink1]✦ Field Survey Slate updated: {title}[/bold pink1]")

    def cutscene_cursor_hide(self):
        '''Hides cursor. Used during cutscenes, but RE-ENABLE after an action if the action is during a cutscene.'''
        Console().show_cursor(False)

    def cutscene_cursor_show(self):
        '''Shows cursor. Used after cutscenes, or DURING one where you type in actions.'''
        Console().show_cursor(True)

    '''The following have to be modified / added to create new cutscenes / quest checks.'''

    def start_cutscene(self, cutscene_name):
        '''Calls cutscene setup and calls the right function for the cutscene. Add new cutscenes in here.'''

        self.cutscene_start_setup()

        cutscene_name = cutscene_name.strip().lower()

        if cutscene_name == "xavier startgame cutscene 01":
            self.xavier_startgame_cutscene_01()

        elif cutscene_name == "jeremy introduction cutscene 02":
            self.jeremy_introduction_cutscene_02()

        elif cutscene_name == "blizzard graveyard jeremy quest cutscene 03":
            self.blizzard_graveyard_jeremy_quest_cutscene_03()

        elif cutscene_name == "abandoned polar bunker jeremy quest cutscene 04":
            self.abandoned_polar_bunker_jeremy_quest_cutscene_04()

        elif cutscene_name == "jeremy quest complete cutscene 05":
            self.jeremy_quest_complete_cutscene_05()

        elif cutscene_name == "permafrost camp return cutscene 06":
            self.permafrost_camp_return_cutscene_06()

    def check_quest_triggers(self):
        '''Checks if the player's current location completes, advances or starts a new quest.
        Add conditions here for TRAVEL only (if player reaches a new location). For action quests, where the player does an action in a location, it can be handled within a cutscene.'''

        # if self.current_quest is None: - redundant
        #     return None #if no quest currently, exit the function

        # Xavier's disappearance? (independent of quests)
        if self.current_location == "Permafrost Camp" and self.left_camp_before == True: 
            # Reset the flag so it only triggers the very first time you come back
            self.left_camp_before = False 
            self.custom_sleep(1.5)
            self.start_cutscene("permafrost camp return cutscene 06")
                
        # Tutorial quest check (check if completed, and start the quest)
        if self.current_quest.title == "Reach the Icy Car Repair Depot":
            if self.current_location == "Icy Car Repair Depot": #if quest condition met and complete:

                self.current_quest.advance_progress(1) #this also finishes the quest

                # tell player they finished the tutorial quest
                self.log("[bold green]✦ Tutorial Complete: You reached the Icy Car Repair Depot.[/bold green]")

                self.custom_sleep(1.5)
                
                # call Jeremy's cutscene and start the new quest #1
                self.start_cutscene("jeremy introduction cutscene 02")

        # Jeremy's quest check
        elif self.current_quest.title == "Retrieve Jeremy's Car Parts":
            if self.current_location == "Blizzard Graveyard":
                self.custom_sleep(1.5)
                self.start_cutscene("blizzard graveyard jeremy quest cutscene 03")

        elif self.current_quest.title == "Retrieve Jeremy's Car Parts" and self.current_quest.current_progress == 2:
            if self.current_location == "Abandoned Polar Bunker 01":

                self.custom_sleep(1.5)
                self.start_cutscene("abandoned polar bunker jeremy quest cutscene 04")

        #Jeremy's quest complete
        elif self.current_quest.title == "Retrieve Jeremy's Car Parts" and self.current_quest.current_progress == 3:
            if self.current_location == "Icy Car Repair Depot":

                self.custom_sleep(1.5)
                self.start_cutscene("jeremy quest complete cutscene 05")       
        
    def xavier_startgame_cutscene_01(self):
        '''The cutscene from the beginning of the game.
        
        Xavier describes the reason for the Ice Age, the goal to reach (Casablanca), subtle foreshadowing with the player questioning why he was left behind.
        He also hands you three quest items.
        You loot his body after he dies.'''


        # waking up, weather, memory, and handing over the envelope
        part_1 = [
            'Violent winds burst through the ridge, tearing at the nylon connectors of the shelter.',
            '[cyan]Snow[/cyan] sprays through an open flap, dusting across a man shivering violently on a frozen bean bag.',
            'His frosted eyes snap open, [b red]bloodshot[/b red] and frantic as his hands claw towards you.',

            PAUSE,
            "[1] Back away slightly",

            '\"Listen to me... there is very little time. The storm will rip this tent into shreds before night!\"',
            "\"All cause of some [b]orbital shift[/b]... Earth's tilt drifted in a natural cycle. You can't blame the ice for being there. It's all just physics in this world.\"",
            "\"My mind... it feels like freezing slush. Can't even remember how long I've been shivering in this tent for. Name's [bold yellow]Xavier[/bold yellow] by the way.\"",

            PAUSE,
            "[1] Shake his ice cold, shivering hand",

            "\"It's nice to meet you. Though we won't have much time together.\"",

            SEPARATOR,

            "[i]You stare at a clothing tag on his flip flops. It reads in red - [b red]Member of Expedition 14[/b red].[/i]",

            SEPARATOR,
            
            f"\"Expedition 14 dashed south for [b green]Casablanca Desert Fortress[/b green]. Rumoured to be {'30' if 'C' in self.settings['temp_unit']['Status'] else '54'} degrees warmer...\"",
            "\"Some say there are [orange]geothermal wells[/orange] that warm your hands up and oil wells with infinite supply. Never been there though.\"",
            "\"[b]You're Expedition 13.[/b] After fourteen left me here, I held out hope to gather enough stragglers to form a thirteenth wave... but nobody else came through. Just you.\"",

            SEPARATOR,
            "\"Over the decades, there have been close to [i]sixty[/i] expeditions... thousands of souls trying to march down this frozen corridor. Most of them vanish.\"",
            "\"Expedition 15 was lost somewhere up in the high mountains—never heard from again. And Expedition 14 left months ago.\"",

            SEPARATOR,
            "\"The pass... it gets blinding out there. The whiteouts swallow a man whole before he can even blink.\"",
            "\"I was right behind the squad when the wind hit us like a wall. Visibility dropped to zero in seconds.\"",
            "\"People started shouting, scattering into the drift... trying to hold onto the sledges, trying not to [cyan]freeze[/cyan].\"",
            "\"In that kind of whiteout, you lose track of everyone. People get separated. It's easy to get left behind when the storm is howling and everyone's just fighting for their own breath...\"",
            "\"[i]Or maybe... maybe the group just didn't look back when I stumbled. Hard to tell what's the blizzard's fault and what's just men running from the cold.[/i]\"",

            SEPARATOR,

            "\"I haven't seen a single soul pass through since they marched past this ridge. With the way things are dying out... you and I might be the last.\"",

            PAUSE,
            "[1] Step closer and kneel by his bean bag",

            'Xavier\'s stiff, [cyan]frostbitten[/cyan] fingers drag a heavy envelope from his inner pocket, thrusting it into your chest.',
            "\"Inside is a note. Sealed with a thick, optical [red]crimson[/red] wax seal. It is your [b red]only credential[/b red] to enter Casablanca.\"",
            "\"Do not break the seal. Do not read whatever is scribbled inside. If the wax fractures, the gate guards treat you as a corpse.\"",

            PAUSE,
            "[1] Take his note - your thumb grazes a faint, waxy texture on the parchment inside"
        ]

        self.log_script(part_1)

        # End the script and add the item to the inventory.
        note_item = Item("Xavier's Wax-Sealed Note", "A sealed note Xavier gave to you as he died. Opening it is not a good idea…", "Quest Special", "Quest", 1, 1, 1, is_quest_item=True, important_information={"seal_intact": True})
        self.add_item_to_inventory(note_item, "satchel")
        self.log(f"[bold green]✦ you add the note to your satchel.[/bold green]")
        self.custom_sleep(1.0)

        # handing over the slate, route list, and backpack
        part_2 = [
            SEPARATOR,
            'He unclips a matte-black e-paper display from his belt, tapping a sensor to register: [dim]EXPEDITION 13 (SOLO)[/dim].',
            f"\"A {self.get_coloured_name('Field Survey Slate & Slate Pen (Unique)', 'Unique')}. Built to survive [red]nine-hundred degrees[/red]. Recharges on a thermal gradient cell anywhere you walk.\"",
            f"\"And a {self.get_coloured_name('Crumpled Route List (Quest Item)', 'Quest Item')}. Only shows the first main leg you will need to reach: [b]Valley Camp 02[/b]. The rest reveals itself once you hit the checkpoint.\"",
            "\"Here, take this old canvas backpack too. You're going to need it to haul your gear out of this wasteland.\"",

            PAUSE,
            f"[1] Take the backpack and equipment:\n{self.get_coloured_name('1 x Field Survey Slate & Slate Pen (Unique)', 'Unique')}\n{self.get_coloured_name('1 x Crumpled Route List (Quest Item)', 'Quest Item')}"
        ]

        self.log_script(part_2)

        # End the script and add the items to the inventory.
        slate_item = Item("Field Survey Slate & Slate Pen", "Made of anodized titanium. Survives years of usage and apparently impossible to burn.", "Unique", "Quest", 1, 1, 1, is_quest_item=True, important_information={"indestructible": True})
        route_item = Item("Crumpled Route List", "Given to you right before Xavier swallowed the aluminium pen. A much needed guide in this environment.", "Quest Special", "Quest", 1, 1, 1, is_quest_item=True, important_information={"unlocked_stage": 1})
        
        self.add_item_to_inventory(slate_item, "satchel")
        self.add_item_to_inventory(route_item, "satchel")
        self.log(f"[bold green]✦ you slide the slate and route list into your satchel, and put on the backpack.[/bold green]")
        self.custom_sleep(1.0)

        # the swallow, death, and looting beat
        part_3 = [
            SEPARATOR,
            'Xavier\'s head lolls backward against the frozen bean bag, his chest hitching in a shallow, hollow wheeze.',
            'Right as his jaw slackens, his hand shoots to his collar with terrifying speed.',
            'He forces a thick, unusually [b]heavy[/b] aluminum pen with [purple]vibrant purple accents[/purple] deep past his teeth, swallowing it whole in a single, violent convulsion.',
            '[i red]A dry, final rattle echoes from his throat, and his body goes dead weight against the canvas.[/i red]',

            PAUSE,
            "[1] Loot Xavier's body - strip his shirt, jeans, flip flops, tuna, and matches"
        ]

        self.log_script(part_3)

        # End the script and add the items to the inventory and equip clothing.
        tuna_item = Item("Can of Tuna", "A regular old can of tuna. Reliable, but has questionable taste.", "Common", "Food", 1, 1, 1, is_quest_item=False, important_information={"Food": 3.0})
        matches_item = Item("Box of Dry Matches", "A handy box of matches that surprisingly still works. Used only in dire situations.", "Uncommon", "Tool", 10, 10, 1, is_quest_item=False)

        self.add_item_to_inventory(tuna_item, "backpack")
        self.add_item_to_inventory(matches_item, "backpack")

        # Add clothing
        self.player.clothing[1] = Item("Ragged T-Shirt", "A black T-shirt with noticeable wear and tear. Feels a bit sketchy to put on.", "Common", "Clothing Top", 200, 200, 1, important_information={"Warmth": 0.03})
        self.player.clothing[2] = Item("Torn Black Jeans", "A pair of bleak jeans gifted by Xavier. It has been through a long journey already.", "Common", "Clothing Bottom", 150, 150, 1, important_information={"Warmth": 0.015})
        self.player.clothing[3] = Item("Flip Flops", "Some rubber flip flops Xavier bought at a gift shop by the beach back before the Ice Age.", "Common", "Clothing Shoes", 50, 50, 1, important_information={"Warmth": 0.005})

        self.log("[bold green]✦ you strip the warm layers off his corpse and add the food and matches to your backpack.[/bold green]")
        self.log("[dim][i]tucked behind his bean bag, your hand knocks a steel flask. oddly, the liquid sloshes unfrozen, though the draft hurries you along.[/i][/dim]")

        self.custom_sleep(1.5)

        # Setup the quest and add the notes to the slate log
        self.add_slate_log(
            "EXPEDITION 13 (SOLO) & XAVIER's DEATH",
            "Xavier died of hypothermia; gave wax credentials, Slate, and Route List to reach Casablanca.",
            "He ingested a thick purple-accented aluminum pen upon death."
        )

        self.current_quest = Quest(
            "Reach the Icy Car Repair Depot",
            "Tutorial Quest",
            "Trek 65 km North-northwest to reach Jeremy's depot.",
            1,
            "In Progress"
        )

        self.cutscene_cursor_show()

    def jeremy_introduction_cutscene_02(self):
        '''Starts Jeremy's cutscene, him introducing you and asking you to complete his quest.'''

        part_01 = [
            "The heavy steel sliding door screeches on [cyan]frozen wheels[/cyan] as you shove it shut behind you.",
            "Inside, the wind dies instantly. The [b]strong[/b] scent of kerosene and coal attacks your nose.",
            f"The [navy_blue]deep numbness[/navy_blue] of your {self.temperature_convert(self.feels_like_temp, self.settings["temp_unit"]["Status"])} degree hands tingle, as your core temperature begins to rise within the shelter.",
            "A shadow peeks behind the raised chassis of a [red]red, clearly battered car[/red].",

            PAUSE,
            "[1] Walk towards the shadow to check it out",

            SEPARATOR,

            "[i]cranking noises[/i]",

            SEPARATOR,

            "The figure suddenly appears from behind the car, clearly surprised anyone made it here.",
            "\"Oh wow. You entered my car depot very abruptly there. I'm [b yellow]Jeremy[/b yellow].\"",
            "\"It's nice seeing people around for once. I've not seen any for months now.\"",

            PAUSE,
            "[1] Tell him it's warm and comfortable in here",

            "[i green]It's so much warmer and more comfortable in here.[/i green]",

            SEPARATOR,
            "[i]chuckles to himself[/i]",
            "\"Yeah... if you ignore the kerosene smells. I'm a mechanic from the old days. Been in here since the [cyan]Ice Age[/cyan] started.\"",

            SEPARATOR,
            
            "\"I was driving North, back towards my house back when the world was [brown]still normal[/brown].\"",
            "\"I noticed the temperature outside [cyan]dropping[/cyan], and instantly panicked.\"",

            PAUSE,
            "[1] Glance over at the red car's engine over there",

            "\"Oh... you're looking at the engine. Well, on the way back, I sped up to try to get back safely, but the car crashed into the side of a [dark green]pine tree[dark green].\"",
            "\"My baby's been missing some components ever since she got [red]damaged[/red]. The piston flew out after I spun out of control, and the internals are scrap.\"",

            PAUSE,
            "[1] Tell him that you're still a bit cold and hungry",

            "[i green]I still feel a bit numb and chilly. And a bit drained to be honest.[/i green]",

            "[i]Your stomach rumbles[/i]",

            "\"[red]Oh?[/red] You should've told me earlier. Here you go - you can take a few cans of my [yellow1]Clam Corn Soup[/yellow1] from my reserves.\"",

            "[i]Jeremy sighs, and hands them over to you.[/i]",

            f"\"Here ya go - {self.get_coloured_name('2 x Can of Clam Corn Soup (Uncommon)', 'Uncommon')}\"",

            PAUSE,
            f"[1] Take the {self.get_coloured_name('2 x Can of Clam Corn Soup (Uncommon)', 'Uncommon')}"
        ]

        self.log_script(part_01)

        soup_item = Item("Can of Clam Corn Soup", "A hearty can of clam and corn soup. Perfect for reminding you when you could actually fish up those clams.", "Uncommon", "Food", 1, 1, 2, is_quest_item=False, important_information={"Food": 2.5})

        self.add_item_to_inventory(soup_item, "backpack")

        part_02 = [
            "The wind howls outside.",

            SEPARATOR,

            "\"If I'm ever going to drive away and out of this valley, this car ain't gonna cut it.\"",
            "\"The whole damn engine parts gotta be replaced. That includes [b yellow]one intact machined piston, and two metal connecting rods[/b yellow].\"",
            "\"I've heard that if you head further north, you might find the components scattered around somewhere.'\"",
            "\"There's a vehicle crash site near [b cyan]Blizzard Graveyard[/b cyan], and if you go all the way up, the piston can be pulled out somewhere in the abandoned bunker up there. Nobody needs it anyways.\"",

            "Jeremy crosses his arms and looks you in the eye.",

            "\"Bring me those three parts, and I'll make it worth your while. I'll hand over three sealed tins of pink salmon—three full rations each—and a pair of thick wool work trousers that'll keep the wind from biting through your denim.\"",

            "\"[b gold]Oh, and on top of that, I'll give you two items you can pick from for your reward when you head back.\""

            "\"You'll have to retrieve those parts to see what it is that I'm talkin' about.\"",

            SEPARATOR,

            "His hands wander towards the exit door's latch, holding it in the [red]locked[/red] position.",

            SEPARATOR,
            "\"So... Are you down to help me? It's your call.\"",

            "[i]His hands [b]grip tightly[/b] onto the latch, seemingly forcing you to say yes - or trapping you in with him.[/i]",

            PAUSE,
            "[1] Accept his quest and head north to retreive Jeremy's car parts"
        
        ]

        self.log_script(part_02)
        # Setup the quest

        self.current_quest = Quest(
            "Retrieve Jeremy's Car Parts",
            "Main Quest",
            "Obtain 2 metal connecting rods and one machined piston and return it to Jeremy.",
            3,
            "parts collected"
        )

        self.cutscene_cursor_show()

    def blizzard_graveyard_jeremy_quest_cutscene_03(self):
        '''When the player reaches the blizzard graveyard with Jeremy's quest active.'''

        part_01 = [
            "[i]You can feel the souls radiating from the graves. Hundreds of them, if not more.[/i]",
            "The wind howls through a maze of snow-covered mounds and half-buried industrial wreckage.",

            SEPARATOR,

            "\"Somewhere out here... two connecting rods,\" you murmur, your teeth chattering violently in the gale.",
            "Squinting through the whiteout, two shapes catch your eye through the drifting snow.",

            SEPARATOR,

            # selection menu with multiple options
            CHOICE_START,

            "[1] Head toward the far end to search an overturned transport hauler",
            "[2] Walk over to a grave mound draped with an oil-stained mechanic's vest",

            CHOICE_END
        ]

        choice = self.log_script(part_01) #gets the option chosen - and displays different things but leading to the same outcome

        if choice == "1":
            # searching the vehicle first
            part_02 = [
                "You trudge through knee-deep drifts toward the far end of the clearing.",
                "A massive cargo hauler lies on its side, its engine compartment cracked open and packed with [cyan]blue ice[/cyan].",
                "Using your hands to chip away the frozen crust, you unbolt an intact [b yellow]metal connecting rod[/b yellow] from the broken block.",

                PAUSE,
                "[1] Pocket the first rod and look around for the second",

                "Scanning the ground, you spot a trail of frozen oil droplets leading away from the wreck.",
                "The trail stops at a lonely snow mound marked with a rusted iron tie and a weathered mechanic's vest.",
                "At the foot of the grave sits an open steel toolbox. Nestled inside the frozen grease rags is the [b yellow]second connecting rod[/b yellow].",

                PAUSE,
                "[1] Take the second rod and wipe the frost off the metal"
            ]
            self.log_script(part_02)

        else:
            # searching the mechanic's vest grave first
            part_02 = [
                "You crunch through the crust toward the lonely mound draped in faded canvas and oil-stained work vest.",
                "A frozen leather tool pouch sits half-buried in the snow beside the cross marker.",
                "You pry the stiff leather flap open. Inside, coated in car grease, is a [b yellow]metal connecting rod[/b yellow].",

                PAUSE,
                "[1] Pocket the first rod and search for where he worked",

                "Looking up from the grave, you notice stiff, frozen bootprints heading toward the far end of the yard.",
                "They lead directly to an overturned cargo hauler with its hood ripped apart.",
                "Inside the hauler's exposed engine compartment, right where the deceased mechanic had been working, rests the [b yellow]second connecting rod[/b yellow].",

                PAUSE,
                "[1] Unseat the second rod from the engine and stow it"
            ]
            self.log_script(part_02)

        # add 2 x metal connecting rods to player satchel
        rod_item = Item(
            "Metal Connecting Rod",
            "Heavy forged steel connecting rods salvaged from the Blizzard Graveyard.",
            "Quest Item",
            "Quest",
            1, 1, 2,
            is_quest_item=True
        )

        self.add_item_to_inventory(rod_item, "satchel")

        self.log(f"[bold green]✦ you add {self.get_coloured_name('2 x Metal Connecting Rods', 'Quest Item')} to your satchel.[/bold green]")

        self.custom_sleep(1.0)

        # from 0/3 to 2/3
        self.current_quest.advance_progress(2)

        self.cutscene_cursor_show()

    def abandoned_polar_bunker_jeremy_quest_cutscene_04(self):
        '''When the player reaches the Abandoned Polar Bunker 01 with Jeremy's quest active and 2/3 progress on the quest.'''

        part_01 = [
            'Slightly dusty glass double doors grind open against a mountain of compacted snow.',
            'You step inside the [cyan]cold[/cyan], concrete interior of Polar Bunker 01. The air inside is chilly like the outside, greatly contrasting with the Car Depot.',
            'At the back end of the room sits an industrial diesel generator, its housing stripped open years ago.',
            
            PAUSE,
            "[1] Walk over to the auxiliary generator block",

            'The heavy backup engine is [cyan]frozen dead[/cyan], its casing cracked wide by expanding ice, and shattering the engine itself into pieces.',
            f"Stuck deep within the engine is the final piece [yellow]Jeremy[/yellow] described: a heavy, precision-machined steel piston - somehow completely intact.",
            'You lean against it using your bodyweight and a thick wooden stick you found outside. The wooden stick snaps, but the piston pops loose.',

            PAUSE,
            f"[1] Extract the {self.get_coloured_name('Machined Piston', 'Quest Item')} and store it",

            "[i green]You breathe a sigh of relief after making sure the piston is not broken.[/i green]"

        ]

        self.log_script(part_01)

        # Add the piston to satchel
        piston_item = Item(
            "Machined Piston",
            "A heavy mechanical piston extracted from a backup generator at the Abandoned Polar Bunker 01.",
            "Quest Item",
            "Quest",
            1, 1, 1,
            is_quest_item=True
        )

        self.add_item_to_inventory(piston_item, "satchel")

        self.log(f"[bold green]✦ you add the {self.get_coloured_name('Machined Piston', 'Quest Item')} to your satchel. All 3 parts are collected![/bold green]")

        self.custom_sleep(1.0)

        # Update from 2/3 to 3/3 done
        self.current_quest.advance_progress(1)

        # player choice of what to do next in the bunker (hinting slightly at the twist at the end)
        part_02 = [
            SEPARATOR,

            "With the piston [green]secured[/green], you widen your gaze to the rest of the room.",
            "To your left, a heavy secondary blast door is sealed tight with an electronic keypad panel flashing [red]red[/red].",
            "To your right, an old school locker dangles open with the door barely clinging on...",

            SEPARATOR,

            CHOICE_START,

            "[1] Search the locker for anything else useful",
            "[2] Approach the sealed blast door and inspect the electronic keypad",
            "[3] Exit and try to get back to [yellow]Jeremy[/yellow] as soon as possible",

            CHOICE_END
        ]

        choice = self.log_script(part_02)

        if choice == "1":
            part_03 = [
                "You rush over to the loose locker and wrench the iron door open.",
                "Inside, there are only [dim]rusted scrap bolts[/dim], [dim]frozen oil filters[/dim], and [dim]shredded packing foam[/dim]. Nothing of value.",
                "You turn back toward the [bold]heavy blast door[/bold] across the room, realizing the keypad is the only way deeper.",
                SEPARATOR
            ]
            self.log_script(part_03)

        # Part 4: Keypad Interaction (Guaranteed to fail on Run 1)
        if choice != "3":
            part_04 = [
                "You stand before the reinforced blast door. An [bold cyan]8-digit authorization display[/bold cyan] blinks softly in the dark.",
                "You have no idea what the code could be.",
                
                PAUSE,
                "[1] Try punching in a random sequence of numbers",
                
                "You tap out a quick sequence on the rubberized buttons...",
                "[bold red]ACCESS DENIED — AUTHORIZATION FAILED.[/bold red]",

                "A harsh mechanical buzzer echoes down the empty corridor. The system locks you out for thirty seconds.",
                "You press your bare fingers against the cold buttons again. Nothing happens. The keypad is [red]completely unresponsive[/red] to guessing.",

                PAUSE,
                "[1] Turn away from the locked door and head back south toward [yellow]Jeremy[/yellow]'s depot",

                "The glass doors automatically slide open as you near it. Your feet and body exit back out to the [cyan]cold[/cyan]."
            ]

            self.log_script(part_04)
        else:
            part_04 = [
                "Your body turns back around towards the howling wind outside.",

                PAUSE,
                "[1] Walk outside to the [cyan]freezing cold[/cyan] and start heading back to [yellow]Jeremy[/yellow]",

                "The glass doors automatically slide open as you near it. Your feet and body exit back out to the [cyan]cold[/cyan]."
            ]

            self.log_script(part_04)

        # self.current_quest.title = "Return to Jeremy with Car Parts"
        # self.current_quest.progress_label = "Ready to Turn In"

        self.cutscene_cursor_show()

    def jeremy_quest_complete_cutscene_05(self):
        '''When you arrive back at the Icy Car Repair Depot at 3/3 progress (with his components). Gives a reward branch (key or bucket hat.)'''

        part_01 = [
            "The [brown]corrugated iron door[/brown] groans open as you slide it aside, stepping out of the [cyan]violent gale[/cyan] into the comfortable warmth of the depot.",
            "[yellow]Jeremy[/yellow] drops his wrench with a sharp metallic clatter, his eyes locking onto your heavy satchel.",
            "\"You're back... and you actually survived the North? Let me see what you pulled out of the [cyan]ice[/cyan].\"",

            PAUSE,
            "[1] Unload the two connecting rods and the heavy machined piston onto the workbench",

            "Jeremy's dusty, oily hands trace over the pitted steel of the piston, running his thumb along its clean crown.",
            "\"I don't believe it. An intact piston and two matching rods... My red baby gonna roar back to life.\"",
            "A wide, exhausted grin breaks across his [orange]grease-streaked[/orange] face. For the first time, he looks [orange]genuinely human[/orange].",
            "\"You held up your end of the bargain, kid. And I'll hold up mine. No more eating dry rations in the dark.\"",

            PAUSE,
            "[1] Accept Jeremy's gratitude and your promised gear",
        ]

        self.log_script(part_01)

        # add all items back in the player's inventory except the quest items
        self.player.satchel = [item for item in self.player.satchel if item.item_name not in ["Metal Connecting Rod", "Machined Piston"]]

        # add the fixed rewards of 2 cans of salmon and thin wool pants
        salmon_item = Item("Can of Salmon", "A switchup to the usual can of tuna. A bit of fishy oil doesn't surprise anyone.", "Uncommon", "Food", 1, 1, 2, is_quest_item=False, important_information={"Food": 3.0})
        pants_item = Item("Thin Wool Pants", "A pair of durable, thermal-woven wool pants. (+7.5% Warmth)", "Uncommon", "Clothing Bottom", 180, 180, 1, important_information={"Warmth": 0.075})
        
        self.add_item_to_inventory(salmon_item, "backpack")
        
        # automatically equips pants
        slot_index = 2 # pants slot

        # temporary variable to store
        old_pants = self.player.clothing[slot_index]
        self.player.clothing[slot_index] = pants_item

        # if no equipped pants add to backpack, otherwise equip
        if old_pants is not None:
            self.add_item_to_inventory(old_pants, "backpack")
        else:
            self.log("[i]You put the new wool pants on.[/i]")

        self.log(f"[bold green]✦ Acquired: {self.get_coloured_name('2 x Can of Salmon', 'Uncommon')} and obtained {self.get_coloured_name('Thin Wool Pants (+7.5% Warmth)', 'Uncommon')}.[/bold green]")

        self.custom_sleep(1.0)

        # choice between bucket hat or key (both have consequences down the line in quests)
        part_02 = [
            SEPARATOR,
            "Jeremy wipes his hands on an oily rag and reaches into his top desk drawer, pulling out two items and slides them out on the wooden table.",
            "\"Much [pink1]love[/pink1], kid. Here's the options of items you can pick from. Both will help you later on if you use them correctly.\"",
            
            SEPARATOR,

            CHOICE_START,

            "[1] Take the [cyan]Knit Bucket Hat[/cyan] (+2.5% Warmth)",
            "[2] Take [magenta]Jeremy's Key[/magenta] [Unique]",

            CHOICE_END
        ]

        choice = self.log_script(part_02)

        if choice == "1":
            hat_item = Item("Knit Bucket Hat", "A thin bucket hat with somewhat of a wool layer on the inside (+2.5% Warmth). Keeps your ears from freezing on the trail.", "Common", "Clothing Head", 100, 100, 1, important_information={"Warmth": 0.025})
            
            # equip to head - temporary variable
            old_head = self.player.clothing[0]

            
            self.player.clothing[0] = hat_item

            # if some headwear equipped, add to backpack instead
            if old_head is not None:
                self.add_item_to_inventory(old_head, "backpack")

            self.log(f"[bold green]✦ You chose the {self.get_coloured_name('Knit Bucket Hat', 'Common')}. Very wise for the ears.[/bold green]")
            
            part_03 = [
                "Jeremy watches you pull the hat down tight.",
                "\"Sensible choice. Keeps the wind off your ears when you hit a [cyan]snowstorm[/cyan].\"",
                "\"That hat ain't too strong, but it can certaintly allow you to fight the wind at [light_sky_blue1]higher altitudes[/light_sky_blue1]. Be safe, okay?\"",

                PAUSE,
                "[1] Nod your head in gratefulness"

            ]

            self.log_script(part_03)

        else:
            key_item = Item("Jeremy's Key", "An indented brass key with the name Jeremy etched into it. Might be useful to other people later.", "Unique", "Quest", 1, 1, 1, is_quest_item=True, important_information={"key_target": "Polar_Bunker_01_Armory"})
            self.add_item_to_inventory(key_item, "satchel")

            self.log(f"[bold green]✦ You accepted {self.get_coloured_name('Jeremy\'s Key', 'Unique')} and slid it into your satchel.[/bold green]")
            
            part_03 = [
                "Jeremy watches you pocket the cold [brown]metal[/brown] key with a knowing nod.",
                "\"That key doesn't keep you [pink1]warm[/pink1], friend. But I heard there are people South that might want this key.\"",
                "\"There's no need to worry about handing it over if you think the trade is worth it. You won't need it yourself anyways.\"",
                
            ]
            self.log_script(part_03)

        # finish quest
        final_wrap = [
            SEPARATOR,

            "\"The road south is long, and the weather's only going to get uglier from here. Take shelter here whenever you loop back, traveler.\"",
            
            PAUSE,
            "[1] Nod farewell to Jeremy and step back out into the [cyan]freezing cold[/cyan]"
        ]
        self.log_script(final_wrap)

        # clear current quest
        self.current_quest = None
        self.log("[bold gold1]✦ Quest Complete: Jeremy's Car Parts finished successfully![/bold gold1]")

        self.cutscene_cursor_show()

    def permafrost_camp_return_cutscene_06(self):
        '''Triggered the first time the player gets back to Permafrost Camp.'''
        
        return_script = [
            "You trudge back up the ridge to where Permafrost Camp had been pitched.",
            "The relentless gale has [i]seemingly[/i] flattened the snowdrifts entirely, scouring the plateau down to hard, blue-white ice.",
            "A few shredded ribbons of the tent connectors whip wildly from a single buried tent stake, but the hollow space between the rocks is completely empty.",
            "A brutal whiteout gust hits you square in the chest, forcing you to turn away before the wind blinds you completely.",
            
            PAUSE,
            "[1] Move slightly away (20m) from the tent to a more covered location"
        ]

        self.log_script(return_script)
        self.cutscene_cursor_show()

    # Template for escape sequences - used for QUOTES in cutscenes "\"Insert quote here\"", but otherwise use "" as normal
    
    def play(self):
        '''The main function to start the game.'''

        #Removes ability to scroll up or down
        sys.stdout.write("\x1b[?1049h\x1b[H")
        sys.stdout.flush()

        # Starting menu
        self.start_menu()

        # Start opening cutscene
        self.start_cutscene("xavier startgame cutscene 01")
        
        while self.player.is_alive() and self.current_location != FINAL_LOCATION: #while player alive and not at destinatioon

            self.update_action_menu_status("Closed") #screen refreshes so action menu becomes closed

            # display interface
            self.refresh_screen()

            # get action (travel, open inventory -> which also comes with further actions, view advanced stats etc)
            action = self.get_action() 

            # performs the actual action - by calling functions
            self.do_action(action)

    def start_menu(self):
        '''Displays a very basic start menu.'''

        error_message = ""

        while True:
            self.clear_screen()

            if error_message != "": #if there is an error message
                print(f"\n[bold red]{error_message}[/bold red]\n") #prints error message in red

            print(f"[bold red]Expedition 13[/bold red]\n")

            print(f"[green][1] Start Game[/green]")
            print(f"[gray][2] Settings[/gray]")

            option = input("\nEnter an option to start.  ").strip()

            if option == "1":
                return None #start the game

            elif option == "2":
                error_message = ""
                self.open_settings_menu(mode="start_menu")

            elif option == "Boiling50":
                print(f"Hidden option unlocked - fast forwarding tutorial.")
                self.typewriter_override = True #removes typewriter for cutscenes
                return None

            else:
                error_message = f"Invalid option."

if __name__ == "__main__":
  survival_game = Game()
  survival_game.play()

        

                
