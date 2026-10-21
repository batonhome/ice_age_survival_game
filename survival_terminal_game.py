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
MAX_FOOD = 8
START_BODY_TEMP = 37.0
FINAL_LOCATION = "Casablanca Desert Fortress"
SIDEBAR_WIDTH = 26 

#Whether the interface has borders.
TOP_INFO_BORDERS = "bold red"
SIDEBAR_BORDERS = "red"



#Hotbar width- affects dialogue box
DIALOGUE_WIDTH = 60
HOTBAR_SPACING = 15

#Symbols that may change
FULL_HEART_SYMBOL = "❤️ "
HALF_HEART_SYMBOL = "💗 "
EMPTY_HEART_SYMBOL = "🩶 "

FULL_FOOD_SYMBOL = "🍔"
EMPTY_FOOD_SYMBOL = "🍽️ "

#Number of rows for the dialogue box
DIALOGUE_TEXT_ROWS = 10

'''Note: to print a chunk of messages in order, first append the message you want to self.current_message_block, then use self.log_chunk_to_single_line.

To print messages inside the dialogue box, use log().

Finally, to print messages outside (and below) the dialogue box, use print() as normal (for things such as input text.)
'''
from time import sleep
from rich import print
from rich.columns import Columns
from rich.panel import Panel
from random import choice, randint, shuffle
from datetime import date, timedelta
from rich.console import Console
from rich.align import Align
from rich.console import Group

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
        '''Increase food level by a certain amount, but not over 8.'''
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
        self.date = date.today()
        self.formatted_date = self.date.strftime("%a, %b %d")
        self.current_stage = 'Morning'
        self.weather = "Clear"
        self.environment_temp = -25.0
        self.feels_like_temp = -25.0
        self.current_location = "Permafrost Camp" #player starts at Permafrost Camp
        self.distance_left = 3500 #km

        #Not game related (directly)
        self.past_dialogue = [" "] * 5
        self.current_message_block = []

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
                                                  
                          
        
    def advance_day(self):
        '''Advances the day counter by 1.'''
        self.day += 1
        self.advance_date()

    def advance_date(self):
        '''Changes the date to match the advance in the day.'''
        self.date = self.date + timedelta(days=1)
        self.formatted_date = self.date.strftime("%a, %b %d") #updates the formatted date
        
    def advance_stage(self):
        '''Advances to the next stage in the day - there are 3 stages in the day - morning, afternoon, and night.'''
        stages = ['Morning', 'Afternoon','Night']
        index = (stages.index(self.current_stage) + 1) % 3 #gets the right index, but makes sure its between 1-3

        self.current_stage = stages[index]
        if self.current_stage == "Morning": #if an entire day was skipped (went from Night -> Morning), then advance the day
            self.advance_day()

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
        symbol_matching = {"Rain":"🌧️ ", "Clear":"🌞", "Cloudy":"☁️ ", "Snowstorm":"🌨️ ", "Strong Winds":"🍃", "Snow":"❄️ ", "Hail":"🧊"} #some emojis have a space after due to a visual bug

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

    def travel_input(self, locations_list):
        '''Gets the input for where the user needs to go (either an index or a name). Accounts for error messages and printing layouts. Takes accessible locations list as input.'''

        all_locations_names = list(self.locations.keys())
        lowercase_all_locations_names = [item.lower() for item in all_locations_names]

        accessible_locations_list_lowercase = [location.lower() for location in locations_list]

        error_message = ""

        #loop ends with return statements instead
        while True: 
            
            #each iteration of the loop REDRAWS the interface, to prevent error messages / prompt messages looking weird
            self.clear_screen()
            self.display_interface()

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

        desired_location = self.travel_input(locations_list)

        self.log(f"You chose to go to {desired_location}!")

        #get direction and distance and display to user
        direction = self.access_destination_specific(desired_location, "direction_to")
        distance = self.access_destination_specific(desired_location, "distance_to")

        self.log(f"You are heading {direction} for {distance} km.")
        
        #update their food bar (every stage needed = 1 bar of food consumed)
        stages_needed = self.access_destination_specific(desired_location, "stages_needed")
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
        top_row = Columns([Panel(f"Day {self.day} | {self.formatted_date}", border_style=TOP_INFO_BORDERS, expand=False),
                           Panel(f"Currently at {self.current_location}", border_style=TOP_INFO_BORDERS, expand=False),
                           Panel(f"{self.get_weather_symbol()} {self.environment_temp}°C", width=14, border_style=TOP_INFO_BORDERS, expand=False)])

        print(top_row)

    def display_sidebar(self):
        '''Within the interface, displays the sidebar - which includes the "buttons" to open the inventory, clothing menu and open the actions menu.'''

        #set fixed width to make sure it looks good
        sidebar_buttons = [Panel("🎒 Open Inventory    ", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False), 
                           Panel("👔 Open Clothing Menu", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False), 
                           Panel("🔧 Actions Menu      ", border_style=SIDEBAR_BORDERS, width=SIDEBAR_WIDTH, expand=False)]

        #prints all of them at once
        print(Align.right(Group(*sidebar_buttons)))

    def get_health_display(self):
        '''Gets the hotbar's health bar display and returns it. Health can either be at 1 or 0.5 increments.'''
        health = self.player.health


        #the variables are the AMOUNT of each heart (total = 10)
        full_hearts = health // 1
        half_hearts = 1 if health % 1 == 0.5 else 0 #if you are on a decimal half heart health, you have 1 half heart, otherwise u have 0

        empty_hearts = 10 - full_hearts - half_hearts

        hearts_string = empty_hearts * EMPTY_HEART_SYMBOL + half_hearts * HALF_HEART_SYMBOL + full_hearts * FULL_HEART_SYMBOL

        return hearts_string

    def get_food_bar_display(self):
        '''Gets the hotbar's food display and returns it. Must be in increments of 1, not 0.5.'''

        #the variables are the AMOUNT of each food (total = 8)
        full_food = self.player.food_level
        empty_food = 8 - full_food

        food_string = empty_food * EMPTY_FOOD_SYMBOL + full_food * FULL_FOOD_SYMBOL 

        return food_string

    def display_hotbar(self):
        '''Within the interface, displays the hotbar (bottom) - which includes the health, food levels, body temperature and symbol.'''

        hearts = self.get_health_display()
        food = self.get_food_bar_display()

        print(f"{hearts}{HOTBAR_SPACING*" "}{food}")

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
        '''Logs text into the upcoming record logs to be displayed later.'''

        if specific_colour == None:
            self.record_past_dialogue(text)
        else:
            self.record_past_dialogue(f"[{specific_colour}]{text}[/{specific_colour}]")

    def log_chunk_to_single_line(self):
        '''Logs a chunk of text as a single log within the records, maintaining the original order. Uses the self.current message block.
        If nothing in current message, do nothing.
        Single chunk of message still should not exceed the DIALOGUE_TEXT_ROWS.'''
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
            total_lines += log.count("\n") + 1 #one row would have no '\n's, so it counts as length 1. 2 rows would have 1 '\n's so length 2 and etc

        while total_lines > DIALOGUE_TEXT_ROWS and len(self.past_dialogue) != 0: #loop while our number of lines exceeds the limit and our log isn't empty
            removed_chunk = self.past_dialogue.pop(0)
            total_lines -= removed_chunk.count("\n") + 1 #same counting system as before

    def display_interface(self, exclusive=False):
        '''Displays the main game's interface - the top info, sidebar, hotbar, dialogue box.'''
        self.display_top_info()
        self.display_sidebar()
        self.display_hotbar()
        if not exclusive: # can toggle off printing the display dialogue box
            self.display_dialogue_box()
        
    def get_action(self):
        '''Get the action from the player. (Travel, open inventory, view advanced stats etc). Returns a string.'''

        return "travel" #temporarily

        pass #WIP

    def do_action(self, action):
        '''Performs the action by calling smaller subroutines'''
        if action == "travel":
            self.travel()

        #WIP

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
            # display interface
            self.clear_screen()
            self.display_interface()

            # get action (travel, open inventory -> which also comes with further actions, view advanced stats etc)
            action = self.get_action() 

            # performs the actual action - by calling functions
            self.do_action(action)

            # update statistics - health, hunger, time of day, day counter etc
            self.update_statistics_to_screen()


if __name__ == "__main__":
  survival_game = Game()
  survival_game.play()

        

                
