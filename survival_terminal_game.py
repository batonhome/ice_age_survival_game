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

from time import sleep
import rich
from random import choice, randint, shuffle

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
        self.current_stage = 'Morning'
        self.weather = "Clear"
        self.environment_temp = -25.0
        self.feels_like_temp = -25.0
        self.current_location = "Permafrost Camp" #player starts at Permafrost Camp
        self.distance_left = 3500 #km


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
        self.day += 1
        
    def advance_stage(self):
        '''Advances to the next stage in the day - there are 3 stages in the day - morning, afternoon, and night.'''
        stages = ['Morning', 'Afternoon','Night']
        index = (stages.index(self.current_stage) + 1) % 3 #gets the right index, but makes sure its between 1-3

        self.current_stage = stages[index]
        if self.current_stage == "Morning": #if an entire day was skipped (went from Night -> Morning), then advance the day
            self.advance_day()

    def randomise_weather(self):
        '''Randomises weather, but ensures it is realistic to the current environmental temperature.'''
        #note: if changing / adding possible weather conditions, remember to change indexes if needed
        possible_weather = ["Rain", "Clear", "Cloudy", "Snowstorm", "Strong Winds", "Snow", "Hail"]

        if self.environment_temp > 4: #if its relatively warmer
            index = randint(0,2) #excludes snow
            
        else: #excludes rain
            index = randint(1, len(possible_weather) - 1)

        self.weather = possible_weather[index]

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

    def travel(self):
        '''Allow player to select from menu options (based on the current location's available nodes) to travel somewhere. Consumes food based on distance. Updates all variables.'''

        #all locations names

        all_locations_names = list(self.locations.keys())
        lowercase_all_locations_names = [item.lower() for item in all_locations_names]

        #find available locations
        
        current_location_info = self.access_current_location_info() #This accesses a location instance - meaning attributes of that location can be accessed
        locations_list = list(current_location_info.accessible_locations.keys()) #finds locations accessible from the current location - keys() returns a list of keys in that dictionary

        # display menu
        print(f"You can travel to the following locations:")

        for index, location in enumerate(locations_list):
            print(f"Location #{index+1}: {location}")

        # input from user, ensure valid
        valid = False
        while not valid:
            desired_location = input("Out of the locations, where would you like to go?\nEnter the location name, or location number.")

            # for if the user inputted a location number
            try:
                location_index = int(desired_location) - 1
                if 0 <= location_index <= len(locations_list) - 1: #valid - within bounds & uses 0 indexing
                    valid = True #exits loop
                else:
                    continue #go through loop again

            # for if the user entered a string for the location name
            except:
                # if the location is in the available list of locations
                lowercase_locations_list = [item.lower() for item in locations_list]
                lowercase_desired_location = desired_location.lower()
                if lowercase_desired_location in lowercase_locations_list:
                    # represents the location's index in the available location's list
                    location_index = lowercase_locations_list.index(lowercase_desired_location)
                    valid = True #exits loop
                else:
                    if lowercase_desired_location in lowercase_all_locations_names:
                        print(f"Uhh... You can't go there from here...")
                    else:
                        print(f"{desired_location} is not a place on this map.")
                    continue #invalid - go through loop again
        
        # gets the location chosen
        desired_location = locations_list[location_index]

        print(f"You chose to go to {desired_location}!")

        #get direction and distance and display to user
        direction = self.access_destination_specific(desired_location, "direction_to")
        distance = self.access_destination_specific(desired_location, "distance_to")

        print(f"You are heading {direction} for {distance} km.")
        
        #update their food bar (every stage needed = 1 bar of food consumed)
        stages_needed = self.access_destination_specific(desired_location, "stages_needed")
        self.player.food_decrease(stages_needed)

        

        # update their location
        self.update_location(desired_location)

        #re-set current location info since we have changed location
        current_location_info = self.locations[self.current_location]

        # update temperature and re-randomise weather (randomise maybe 50% of the time)
        self.environment_temp = self.access_current_location_specific("temp") #Location class attribute - not Game class attribute
        self.randomise_weather()
        self.update_feels_like_temp()

    def display_interface(self):
        '''Displays the main game's interface.'''
        pass #WIP

    def get_action(self):
        '''Get the action from the player. (Travel, open inventory, view advanced stats etc). Returns a string.'''
        pass #WIP

    def do_action(self, action):
        '''Performs the action by calling smaller subroutines'''
        if action == "travel":
            self.travel()

        #WIP

    def update_statistics(self):
        '''Update statistics - health, hunger, time of day, day counter etc.'''

    def play(self):
        '''The main function to start the game.'''

        while self.player.is_alive() and self.current_location != FINAL_LOCATION: #while player alive and not at destinatioon
            # display interface
            self.display_interface()

            # get action (travel, open inventory -> which also comes with further actions, view advanced stats etc)
            action = self.get_action()

            # performs the actual action - by calling functions
            self.do_action(action)

            # update statistics - health, hunger, time of day, day counter etc
            self.update_statistics()

            




        

                
