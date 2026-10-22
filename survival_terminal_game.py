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
HALF_HEART_SYMBOL = "💗 "
EMPTY_HEART_SYMBOL = "🩶 "

FULL_FOOD_SYMBOL = "🍔"
EMPTY_FOOD_SYMBOL = "🍽️ "

#Number of rows for the dialogue box
DIALOGUE_TEXT_ROWS = 10

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
        self.inventory = ["Canned tuna", "Match"]
        self.clothing = [None, "Nike t-shirt", None, "Flip flops"]

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
    def __init__(self, name, distance_left, temp, description, accessible_locations):
        self.name = name
        self.distance_left = distance_left
        self.temp = temp
        self.description = description
        
        # a dictionary with the accessible location with a nested dictionary to show more info (Distance to that location, the direction, the stages of the day taken, and the requirements)
        self.accessible_locations = accessible_locations 
        
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
        self.distance_left = 3500 #km

        #Not game related (directly)
        self.past_dialogue = [" "] * 5 #when the game starts, there is no past dialogue
        self.current_message_block = [] #Preferably don't use the log_chunk thing
        self.action_menu_open = False

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
        self.locations = {"Permafrost Camp" : Location("Permafrost Camp", 3500, -25.0, "A cold, brutal camp with scraps of resources and an abandoned shelter.",
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
                        "Lakeside Castle Ruins" : Location("Lakeside Castle Ruins", 3400, -24.0, "A castle ruins by the frozen lake. No signs of life here.",
                                                 {"Permafrost Camp" : 
                                                  {
                                                    "distance_to" : 25,
                                                    "direction_to" : "Northeast",
                                                    "stages_needed" : 1,
                                                    "requirements" : None
                                                  }
                                                
                                                
                                                }),

                        #--------------------------------------------------------------------
                        "Icy Car Repair Depot" : Location("Icy Car Repair Depot", 3550, -26.0, "A car repair depot operated by Jeremy, a local survivor. Locals say he's a talent.",
                                                 {"Permafrost Camp" : 
                                                  {
                                                    "distance_to" : 65,
                                                    "direction_to" : "South-southeast",
                                                    "stages_needed" : 3,
                                                    "requirements" : None
                                                 },

                                                }),
                        }

    def open_settings_menu(self):
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
            self.refresh_screen()
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

        self.refresh_screen()

        # Conditions for each setting

        # Get info about the setting (chosen_option is the setting_key)
        display_name = self.settings[chosen_option]["Display Name"]
        status = self.settings[chosen_option]["Status"]
        available_options = self.settings[chosen_option]["Available Options"]

        # Setting 1 type -> for any on / off settings

        if status in [True, False]: # add or statements for any toggleable (true/false) settings
            self.toggle_setting(chosen_option) #Inverts the setting
            new_status = self.settings[chosen_option]["Status"]

            status_name = self.find_key_from_valueue(available_options, new_status) #Gets the status name from the status 

            print(f"You toggled {status_name.lower()} {display_name.lower()}. ")
            
        else: # Setting 2 type -> string or number (many options) based settings

            error_message = ""

            while True:
                self.refresh_screen()
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
        sleep(1)
        
        # self.refresh_screen()

        print("[white]Exit or continue changing settings?[/white] ([bold red][u]E[/u][/bold red]xit / [bold green][u]C[/u][/bold green]ontinue): ", end="")
        setting_exit = input()

        if setting_exit.upper().strip() == "E":
            return None # exit
        else:
            self.open_settings_menu()

    def clean_value(self, value):
        '''Removes degree symbol from value.'''
        return str(value).lower().replace("°", "").replace("deg", "").strip()

    def find_key_from_valueue(self, dictionary, value):
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

    def advance_stages(self, stages):
        '''Advances many stages.'''
        for _ in range(stages):
            self.advance_stage()

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
        sleep(REAL_TIME_PER_STAGE)

        rest_cutscene_message = self.get_rest_message()
        self.log(rest_cutscene_message)

        sleep(3 * REAL_TIME_PER_STAGE)

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
        self.advance_stages(3) #which also may randomise weather

        
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

        sleep(REAL_TIME_PER_STAGE)

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

    def travel_input(self, locations_list):
        '''Gets the input for where the user needs to go (either an index or a name). Accounts for error messages and printing layouts. Takes accessible locations list as input.'''

        all_locations_names = list(self.locations.keys())
        lowercase_all_locations_names = [item.lower() for item in all_locations_names]

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
        sleep(time_wait)

        # make it say days if plural, day if not plural
        plural = 's' if days_needed != 1 else ''
        
        self.log(f"You arrived in {desired_location} after {days_needed} day{plural} of travel from {origin_location}.")
        
        #update their food bar (every stage needed = 1 bar of food consumed)
        
        self.player.food_decrease(stages_needed)

        # update the day counter / stages
        self.advance_stages(stages_needed)

        # update their location
        self.update_location(desired_location)

        #re-set current location info since we have changed location
        current_location_info = self.locations[self.current_location]

        # update temperature and re-randomise weather (randomise maybe 50% of the time)
        self.environment_temp = self.access_current_location_specific("temp") #Location class attribute - not Game class attribute
        self.randomise_weather()
        self.update_feels_like_temp()

    def display_top_info(self):
        '''Within the interface, displays specifically the top row - including the day counter, weather, stage counter, temperature and location.'''
        top_row = Columns([Panel(f"Day {self.day} | {self.current_stage} | {self.formatted_date}", border_style=TOP_INFO_BORDERS, expand=False),
                           Panel(f"Currently at {self.current_location}", border_style=TOP_INFO_BORDERS, expand=False),
                           Panel(f"{self.get_weather_symbol()} {self.temperature_convert(self.feels_like_temp, self.settings["temp_unit"]["Status"])}", width=14, border_style=TOP_INFO_BORDERS, expand=False)])

        print(top_row)

    def display_sidebar(self):
        '''Within the interface, displays the sidebar - which includes the "buttons" to open the inventory, clothing menu and open the actions menu.'''

        if self.action_menu_open == False: #helps user open action menu if not open
            additional_text = "[dim]\nPress Enter to Open[/dim]"
        else:
            additional_text = ""

        #set fixed width to make sure it looks good
        sidebar_buttons = [Panel("🎒 Open Inventory    ", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False), 
                           Panel("👔 Open Clothing Menu", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False), 
                           Panel(f"🔧 Actions Menu      {additional_text}", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False)]

        #prints all of them at once
        print(Align.right(Group(*sidebar_buttons)))

    def get_health_display(self):
        '''Gets the hotbar's health bar display and returns it. Health can either be at 1 or 0.5 increments.'''
        health = self.player.health


        #the variables are the AMOUNT of each heart (total = 10)
        full_hearts = health // 1
        half_hearts = 1 if health % 1 == 0.5 else 0 #if you are on a decimal half heart health, you have 1 half heart, otherwise u have 0

        empty_hearts = MAX_HEALTH - full_hearts - half_hearts

        hearts_string = empty_hearts * EMPTY_HEART_SYMBOL + half_hearts * HALF_HEART_SYMBOL + full_hearts * FULL_HEART_SYMBOL

        return hearts_string

    def get_food_bar_display(self):
        '''Gets the hotbar's food display and returns it. Must be in increments of 1, not 0.5.'''

        #the variables are the AMOUNT of each food (total = MAX_FOOD)
        full_food = self.player.food_level
        empty_food = MAX_FOOD - full_food

        food_string = empty_food * EMPTY_FOOD_SYMBOL + full_food * FULL_FOOD_SYMBOL 

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
        '''Displays the dialogue box within the interface at the bottom, with the 5 most recent messages (from most recent at the top to least at the bottom.)'''

        # reverses the past dialogue (to make it go from recent at lower indexes)
        lines = self.past_dialogue[::-1][:DIALOGUE_TEXT_ROWS]

        styled_lines = []

        #style the most recent like bold white and everything else gray
        for index, line in enumerate(lines):
            if index == 0: #if most recent
                styled_lines.append(f"[bold white]{line}[/bold white]")
            else:
                styled_lines.append(f"[dim]{line}[/dim]")

        #joins a string and in between them adding newlines
        dialogue_string = "\n".join(styled_lines)

        dialogue_box = Panel(f"{dialogue_string}", width=DIALOGUE_WIDTH, height=DIALOGUE_TEXT_ROWS + 2) # +2 for borders

        print(dialogue_box)

    def log(self, text, specific_colour=None):
        '''Logs text into the upcoming record logs to be displayed later.
        If typewriter mode is on, it uses sleep() and displays the messages character by character by refreshing the screen each time - like how a video works.'''

        # For any mode just log into the records as normal

        typewriter = self.settings["typewriter"]["Status"] #grabs from settings instead.

        delay = float(self.settings["typewriter_speed"]["Status"]) #grabs from settings
        
        if specific_colour == None:
            self.record_past_dialogue(text)
        else:
            self.record_past_dialogue(f"[{specific_colour}]{text}[/{specific_colour}]")

        if not typewriter:
            return None # ends the function, since if the mode is off we dont need the typewriter

        #Typewriter code

        self.past_dialogue[-1] = "" # makes the message typed empty, so it can start printing char by char
        self.refresh_screen()

        for character in text:
            self.past_dialogue[-1] = self.past_dialogue[-1] + (f"[{specific_colour}]{character}[/{specific_colour}]" if specific_colour != None else character)
            #adds one character, then refreshes the screen after a delay
            sleep(delay)
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

            "6":"close",
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
            print("  [6] Close Action Menu")

            if error_message != "": #if there was an error in the last loop:
                print(f"\n[bold red]{error_message}[/bold red]")

            desired_action = input("\nEnter a choice or number.").strip().lower()

            if desired_action in valid_actions.keys(): #if the action is in the valid actions dictionary
                return valid_actions[desired_action] #return the requested action

            #otherwise give the error message

            error_message = f"'{desired_action}' is not a valid action. Choose 1-4 or type the command name."

    def open_inventory_menu(self):
        '''Opens the inventory menu.'''
        pass #WIP

    def view_detailed_stats(self):
        '''Opens a menu of detailed stats.'''
        pass #WIP

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

        elif action == "close":
            self.update_action_menu_status("Closed")
            self.refresh_screen()

    def update_statistics_to_screen(self):
        '''Update statistics - health, hunger, time of day, day counter etc.'''
        pass

    def play(self):
        '''The main function to start the game.'''

        '''Main logic:
        
        1. For text displayed onto the screen, first log it into the records list.
        2. After each turn, display it all at once.
        
        '''

        while self.player.is_alive() and self.current_location != FINAL_LOCATION: #while player alive and not at destinatioon

            self.update_action_menu_status("Closed") #screen refreshes so action menu becomes closed

            # display interface
            self.refresh_screen()

            # get action (travel, open inventory -> which also comes with further actions, view advanced stats etc)
            action = self.get_action() 

            # performs the actual action - by calling functions
            self.do_action(action)

            # update statistics - health, hunger, time of day, day counter etc
            self.update_statistics_to_screen()


if __name__ == "__main__":
  survival_game = Game()
  survival_game.play()

        

                
