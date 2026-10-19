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
    def __init__(self, name, temp, distance_left, accessible_locations):
        self.name = name
        self.distance_left = distance_left
        self.temp = temp
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
        self.current_location = "Stockholm"
        self.distance_left = 3427 #km


        # a dictionary of locations / nodes - to add new locations: -> add name, temp, distance to finish, accessible locations (which is a dictionary)
        self.locations = {"Stockholm" : Location("Stockholm", 3427, -25.0, 
                                                 {"Sodertalje (Outer Stockholm)" : 
                                                  {
                                                    "distance_to" : 25,
                                                    "direction_to" : "Southwest",
                                                    "stages_needed" : 1,
                                                    "requirements" : "None"
                                                 },
                                                 
                                                  "Uppsala (Outer Stockholm)" : 
                                                  {
                                                    "distance_to" : 65,
                                                    "direction_to" : "North-northwest",
                                                    "stages_needed" : 3,
                                                    "requirements" : "None"
                                                  }
                                                 }),
                        #for each location on the map, add the things above here
                        "Sodertalje (Outer Stockholm)" : Location("Sodertalje (Outer Stockholm)", 3400, -24.0, 
                                                 {"Stockholm" : 
                                                  {
                                                    "distance_to" : 25,
                                                    "direction_to" : "Northeast",
                                                    "stages_needed" : 1,
                                                    "requirements" : "None"
                                                  }
                                                # #NEED to add another place after sodertalje
                                                 
                                                #   "Uppsala (Outer Stockholm)" : 
                                                #   {
                                                #     "distance_to" : 65,
                                                #     "direction_to" : "North-northwest",
                                                #     "stages_needed" : 3,
                                                #     "requirements" : "None"
                                                #   }
                                                }),
                        "Uppsala (Outer Stockholm)" : Location("Uppsala (Outer Stockholm)", 3455, -26.0, 
                                                 {"Stockholm" : 
                                                  {
                                                    "distance_to" : 65,
                                                    "direction_to" : "South-southeast",
                                                    "stages_needed" : 3,
                                                    "requirements" : "None"
                                                 },
                                                # need to add somewhere up from Uppsala
                                                 
                                                #   "Uppsala (Outer Stockholm)" : 
                                                #   {
                                                #     "distance_to" : 65,
                                                #     "direction_to" : "North-northwest",
                                                #     "stages_needed" : 3,
                                                #     "requirements" : "None"
                                                #   }
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
            self.weather = possible_weather[index]
        else:
            index = randint(1, len(possible_weather) - 1)

    def get_feels_like_temp(self):
        '''Gets the rough temperature felt by the player - affected by weather, time of day, and environmental temperature.'''
        weather_effects = {"Rain":-3, "Clear":2, "Cloudy":0, "Snowstorm":-4, "Strong Winds":-2, "Snow":-6, "Hail":-6} #how each weather should affect the experienced temp
        stage_effects = {"Morning":-1, "Afternoon":4, "Night":-3} #how each stage of the day should affect the experienced temp

        self.feels_like_temp = self.environment_temp + weather_effects[self.weather] + stage_effects[self.current_stage]

    def find_available_locations(self):
        '''Returns a list of available locations from one location.'''
        routes = list(self.locations[self.current_location].accessible_locations) #each location you index (e.g. Stockholm) is an object, so it has accessible properties
        return routes

    def travel(self):
        '''Allow player to select from menu options (based on the current location's available nodes) to travel somewhere. Consumes food based on distance.'''
        #find available locations
        # display menu
        # input from user, ensure valid
        # update their location, their food bar (maybe every 10km is 1 bar of food consumed? so no more than 80km at once)
        # update temperature and re-randomise weather (randomise maybe 50% of the time)
        




        

                
