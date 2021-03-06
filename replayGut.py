#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# coding: utf-8

import json
import os
import copy
import math
import numpy as np
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from io import BytesIO
from collections import defaultdict, Counter
from datetime import datetime
from traceback import print_exc
from pandas import DataFrame
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import sc2reader
from sc2reader.engine.plugins import APMTracker, ContextLoader, SelectionTracker, PACAnalyzer
from sc2reader.events import PlayerStatsEvent, UnitBornEvent, UnitDiedEvent, UnitDoneEvent, UnitTypeChangeEvent, UpgradeCompleteEvent, GetControlGroupEvent, SetControlGroupEvent, AddToControlGroupEvent
import urllib.request

# ======================================================================================================================
# Set source_path to your replay repository directory
# ======================================================================================================================

# Source of replay files
#source_path = "reps_HSC_xviii/"
source_path = "/Users/hubertplisiecki/PycharmProjects/untitled/reps"

# Used for debugging when filtering out replay files (cleanup)
file_search_stats = {
    "single": 0,
    "double": 0
    }
file_search_duplicates_timestamps = []

# ======================================================================================================================
# Main loop over replay files
# ======================================================================================================================

for rep in os.listdir(source_path):
    if rep != ".DS_Store":  # This line is unnecessary in windows
        # Used for debugging when filtering out replay files (cleanup)
        removeFromReps = False

        # Replay file open and read
        fh = open(source_path + "/" + rep, 'rb')
        data_1 = BytesIO(fh.read())

        # Some extra code here helps catch setup errors
        try:
            replay_file = data_1
        except NameError:
            print('\n'
                  'SETUP ERROR: Please follow the directions to add a .SC2Replay file and use\n'
                  '             "Insert to code" to set the data_1 variable to the resulting bytes.\n'
                  '             You may need to rename the data_* variable.')
            raise

# ======================================================================================================================
# Read the replay file into the sc2reader
# ======================================================================================================================

        replay = sc2reader.load_replay(
            replay_file,
            engine=sc2reader.engine.GameEngine(plugins=[ContextLoader(), APMTracker(), SelectionTracker(), PACAnalyzer()]))

        # Print out basic replay data
        print("\n\n****************************\nReplay successfully loaded.\n")
        print (source_path + rep + "\n")
        print("Date: %s" % replay.date)
        print("Map Name: " + replay.map_name)
        print("Match time: " + str(replay.game_length.mins) + ":" + str(replay.game_length.secs))
        print("Frames (at 16fps): " + str(replay.frames))
        print("PID:" + str(player.pid for player in replay.players))




# ======================================================================================================================
# Establish some unit and building groups
# ======================================================================================================================

        VESPENE_UNITS = ["Assimilator", "Extractor", "Refinery"]
        SUPPLY_UNITS = ["Overlord", "Overseer", "Pylon", "SupplyDepot", "SupplyDepotLowered"]
        WORKER_UNITS = ["Drone", "Probe", "SCV", "MULE"]
        BASE_UNITS = ["CommandCenter", "Nexus", "Hatchery", "Lair", "Hive", "PlanetaryFortress", "OrbitalCommand"]
        GROUND_UNITS = ["Barracks", "Factory", "GhostAcademy", "Armory", "RoboticsBay", "RoboticsFacility", "TemplarArchive",
                        "DarkShrine", "WarpGate", "SpawningPool", "RoachWarren", "HydraliskDen", "BanelingNest", "UltraliskCavern",
                        "LurkerDen", "InfestationPit"]
        AIR_UNITS = ["Starport", "FusionCore", "RoboticsFacility", "Stargate", "FleetBeacon", "Spire", "GreaterSpire"]
        TECH_UNITS = ["EngineeringBay", "Armory", "GhostAcademy", "TechLab", "FusionCore", "Forge", "CyberneticsCore",
                      "TwilightCouncil", "RoboticsFacility", "RoboticsBay", "FleetBeacon", "TemplarArchive", "DarkShrine",
                      "SpawningPool", "RoachWarren", "HydraliskDen", "BanelingNest", "UltraliskCavern", "LurkerDen", "Spire",
                      "GreaterSpire", "EvolutionChamber", "InfestationPit"]
        ARMY_UNITS = ["Marine", "Colossus", "InfestorTerran", "Baneling", "Mothership", "MothershipCore", "Changeling", "SiegeTank", "Viking", "Reaper",
                      "Ghost", "Marauder", "Thor", "Hellion", "Hellbat", "Cyclone", "Liberator", "Medivac", "Banshee", "Raven", "Battlecruiser", "Nuke", "Zealot",
                      "Stalker", "HighTemplar", "Disruptor", "DarkTemplar", "Sentry", "Phoenix", "Carrier", "Oracle", "VoidRay", "Tempest", "WarpPrism", "Observer",
                      "Immortal", "Adept", "Zergling", "Overlord", "Hydralisk", "Mutalisk", "Ultralisk", "Roach", "Infestor", "Corruptor",
                      "BroodLord", "Queen", "Overseer", "Archon", "Broodling", "InfestedTerran", "Ravager", "Viper", "SwarmHost", "WidowMine"]
        ARMY_AIR = ["Mothership", "MothershipCore", "Viking", "Liberator", "Medivac", "Banshee", "Raven", "Battlecruiser",
                    "Viper", "Mutalisk", "Phoenix", "Oracle", "Carrier", "VoidRay", "Tempest", "Observer", "WarpPrism", "BroodLord",
                    "Corruptor", "Observer", "Overseer"]
        ARMY_GROUND = [k for k in ARMY_UNITS if k not in ARMY_AIR]

        ARMY_UNITS_COST = {"Marine":1,
                           "SiegeTank":3,
                           "Viking":2,
                           "Reaper":1,
                           "Ghost":2,
                           "Marauder":2,
                           "Thor":6,
                           "Hellion":2,
                           "Hellbat":2,
                           "Cyclone":3,
                           "Liberator":3,
                           "Medivac":2,
                           "Banshee":3,
                           "Raven":2,
                           "Battlecruiser":6,
                           "WidowMine":2,
                           "Nuke":0,

                           "Zergling":0.5,
                           "Broodling":0,
                           "Overlord":0,
                           "Queen":2,
                           "Ultralisk":6,
                           "Hydralisk":2,
                           "Mutalisk":2,
                           "Baneling":0.5,
                           "Changeling":0,
                           "Corruptor":2,
                           "Viper":3,
                           "Infestor":2,
                           "Roach":2,
                           'Zealot':2,
                           'Stalker':2,
                           'Sentry':2,
                           'Adept':2,
                           'HighTemplar':2,
                           'DarkTemplar':2,
                           'Immortal':4,
                           'Colossus':6,
                           'Disruptor':3,
                           'Phoenix':2,
                           'VoidRay':4,
                           'Oracle':3,
                           'Carrier':6,
                           'Tempest':5
                           }

# ======================================================================================================================
# Establish event parsers
# ======================================================================================================================

        def handle_count(caller, event, key, add_value, start_val=0):
            if len(caller.players[event.unit.owner.pid][key]) == 0:
                caller.players[event.unit.owner.pid][key].append((0, 0))
            # Get the last value
            last_val = caller.players[event.unit.owner.pid][key][-1][1]
            caller.players[event.unit.owner.pid][key].append((event.frame, last_val + add_value))

        def handle_expansion_events(caller, event):
            if type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in BASE_UNITS:
                    caller.players[event.unit.owner.pid]["expansion_event"].append((event.frame, "+", unit))
                    handle_count(caller, event, "expansion_buildings", 1, start_val=1)
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in BASE_UNITS:
                    caller.players[event.unit.owner.pid]["expansion_event"].append((event.frame, "-", unit))
                    handle_count(caller, event, "expansion_buildings", -1, start_val=1)
            elif type(event) is UnitTypeChangeEvent:
                if event.unit.name in BASE_UNITS:
                    caller.players[event.unit.owner.pid]["expansion_event"].append((event.frame, "*", event.unit.name))

        def handle_worker_events(caller, event):
            if type(event) is PlayerStatsEvent:
                caller.players[event.pid]["workers_active"].append((event.frame, event.workers_active_count))
            elif type(event) is UnitBornEvent:
                unit = str(event.unit).split()[0]
                if unit in WORKER_UNITS:
                    caller.players[event.control_pid]["worker_event"].append((event.frame, "+", unit))
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in WORKER_UNITS:
                    caller.players[event.unit.owner.pid]["worker_event"].append((event.frame, "-", unit))

        def handle_supply_events(caller, event):
            if type(event) is PlayerStatsEvent:
                caller.players[event.pid]["supply_available"].append((event.frame, int(event.food_made)))
                caller.players[event.pid]["supply_consumed"].append((event.frame, int(event.food_used)))
                utilization = 0 if event.food_made == 0 else event.food_used / event.food_made
                caller.players[event.pid]["supply_utilization"].append((event.frame, utilization))
                utilization_fixed = event.food_used / 200 if event.food_made >= 200 else utilization
                caller.players[event.pid]["supply_utilization_fixed"].append((event.frame, utilization_fixed))
                worker_ratio = 0 if event.food_used == 0 else event.workers_active_count / event.food_used
                caller.players[event.pid]["worker_supply_ratio"].append((event.frame, worker_ratio))
                worker_ratio_fixed = event.workers_active_count / 200 if event.food_made >= 200 else worker_ratio
                caller.players[event.pid]["worker_supply_ratio"].append((event.frame, worker_ratio_fixed))
            elif type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in SUPPLY_UNITS:
                    caller.players[event.unit.owner.pid]["supply_event"].append((event.frame, "+", unit))
            elif type(event) is UnitBornEvent:
                # Specifically for Overlord
                unit = str(event.unit).split()[0]
                if unit == "Overlord":
                    caller.players[event.control_pid]["supply_event"].append((event.frame, "+", unit))
            elif type(event) is UnitDiedEvent:
                # Buildings/ Overlord/Overseer
                unit = str(event.unit).split()[0]
                if unit in SUPPLY_UNITS:
                    caller.players[event.unit.owner.pid]["supply_event"].append((event.frame, "-", unit))
            elif type(event) is UnitTypeChangeEvent:
                if event.unit_type_name == "Overseer":
                    caller.players[event.unit.owner.pid]["supply_event"].append((event.frame, "*", event.unit_type_name))

        def handle_vespene_events(caller, event):
            if type(event) is PlayerStatsEvent:
                caller.players[event.pid]["vespene_available"].append((event.frame, event.vespene_current))
                caller.players[event.pid]["vespene_collection_rate"].append((event.frame, event.vespene_collection_rate))
                vesp_per_worker = 0 if event.workers_active_count == 0 else event.vespene_collection_rate / event.workers_active_count
                caller.players[event.pid]["vespene_per_worker_rate"].append((event.frame, vesp_per_worker))
                caller.players[event.pid]["vespene_cost_active_forces"].append((event.frame, event.vespene_used_active_forces))
                caller.players[event.pid]["vespene_spend"].append((event.frame, event.vespene_used_current))
                caller.players[event.pid]["vespene_value_current_technology"].append((event.frame, event.vespene_used_current_technology))
                caller.players[event.pid]["vespene_value_current_army"].append((event.frame, event.vespene_used_current_army))
                caller.players[event.pid]["vespene_value_current_economic"].append((event.frame, event.vespene_used_current_economy))
                caller.players[event.pid]["vespene_queued"].append((event.frame, event.vespene_used_in_progress))
                caller.players[event.pid]["vespene_queued_technology"].append((event.frame, event.vespene_used_in_progress_technology))
                caller.players[event.pid]["vespene_queued_army"].append((event.frame, event.vespene_used_in_progress_technology))
                caller.players[event.pid]["vespene_queued_economic"].append((event.frame, event.vespene_used_in_progress_economy))
            elif type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in VESPENE_UNITS:
                    caller.players[event.unit.owner.pid]["vespene_event"].append((event.frame, "+", unit))
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in VESPENE_UNITS:
                    caller.players[event.unit.owner.pid]["vespene_event"].append((event.frame, "-", unit))

        def handle_resources_events(caller, event):
            if type(event) is PlayerStatsEvent:
                caller.players[event.pid]["mineral_destruction"].append((event.frame, event.minerals_killed))
                caller.players[event.pid]["mineral_destruction_army"].append((event.frame, event.minerals_killed_army))
                caller.players[event.pid]["mineral_destruction_economic"].append((event.frame, event.minerals_killed_economy))
                caller.players[event.pid]["mineral_destruction_technology"].append((event.frame, event.minerals_killed_technology))
                caller.players[event.pid]["mineral_loss"].append((event.frame, event.minerals_lost))
                caller.players[event.pid]["mineral_loss_army"].append((event.frame, event.minerals_lost_army))
                caller.players[event.pid]["mineral_loss_economic"].append((event.frame, event.minerals_lost_economy))
                caller.players[event.pid]["mineral_loss_technology"].append((event.frame, event.minerals_lost_technology))

                caller.players[event.pid]["vespene_destruction"].append((event.frame, event.vespene_killed))
                caller.players[event.pid]["vespene_destruction_army"].append((event.frame, event.vespene_killed_army))
                caller.players[event.pid]["vespene_destruction_economic"].append((event.frame, event.vespene_killed_economy))
                caller.players[event.pid]["vespene_destruction_technology"].append((event.frame, event.vespene_killed_technology))
                caller.players[event.pid]["vespene_loss"].append((event.frame, event.vespene_lost))
                caller.players[event.pid]["vespene_loss_army"].append((event.frame, event.vespene_lost_army))
                caller.players[event.pid]["vespene_loss_economic"].append((event.frame, event.vespene_lost_economy))
                caller.players[event.pid]["vespene_loss_technology"].append((event.frame, event.vespene_lost_technology))

        def handle_ground_events(caller, event):
            if type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in GROUND_UNITS:
                    count_name = "_".join(["building", unit, "count"])
                    caller.players[event.unit.owner.pid]["ground_building"].append((event.frame, "+", unit))
                    handle_count(caller, event, count_name, 1)
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in GROUND_UNITS:
                    count_name = "_".join(["building", unit, "count"])
                    caller.players[event.unit.owner.pid]["ground_building"].append((event.frame, "-", unit))
                    handle_count(caller, event, count_name, -1)
            elif type(event) is UnitTypeChangeEvent:
                if event.unit_type_name == "LurkerDen":
                    count_name = "_".join(["building", event.unit_type_name, "count"])
                    caller.players[event.unit.owner.pid]["ground_building"].append((event.frame, "*", event.unit_type_name))
                    handle_count(caller, event, count_name, 1)

        def handle_air_events(caller, event):
            if type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in AIR_UNITS:
                    count_name = "_".join(["building", unit, "count"])
                    caller.players[event.unit.owner.pid]["air_building"].append((event.frame, "+", unit))
                    handle_count(caller, event, count_name, 1)
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in AIR_UNITS:
                    count_name = "_".join(["building", unit, "count"])
                    caller.players[event.unit.owner.pid]["air_building"].append((event.frame, "-", unit))
                    handle_count(caller, event, count_name, -1)
            elif type(event) is UnitTypeChangeEvent:
                if event.unit_type_name == "GreaterSpire":
                    count_name = "_".join(["building", event.unit_type_name, "count"])
                    caller.players[event.unit.owner.pid]["air_building"].append((event.frame, "*", event.unit_type_name))
                    handle_count(caller, event, count_name, 1)

        def handle_unit_events(caller, event):
            if type(event) is UnitBornEvent:
                unit = event.unit_type_name
                if unit in ARMY_UNITS:
                    unit_count_name = "_".join(["unit", unit, "count"])
                    caller.players[event.control_pid]["army_event"].append((event.frame, "+", unit))
                    handle_count(caller, event, unit_count_name, 1)
                    if unit in ARMY_AIR:
                        handle_count(caller, event, "army_air", 1)
                    elif unit in ARMY_GROUND:
                        handle_count(caller, event, "army_ground", 1)
                    handle_count(caller, event, "army_count", 1)
            elif type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in ARMY_UNITS:
                    unit_count_name = "_".join(["unit", unit, "count"])
                    caller.players[event.unit.owner.pid]["army_event"].append((event.frame, "+", unit))
                    handle_count(caller, event, unit_count_name, 1)
                    if unit in ARMY_AIR:
                        handle_count(caller, event, "army_air", 1)
                    elif unit in ARMY_GROUND:
                        handle_count(caller, event, "army_air", 1)
                    handle_count(caller, event, "army_count", 1)
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in ARMY_UNITS:
                    unit_count_name = "_".join(["unit", unit, "count"])
                    caller.players[event.unit.owner.pid]["army_event"].append((event.frame, "-", unit))
                    if unit in ARMY_AIR:
                        handle_count(caller, event, "army_air", -1)
                    elif unit in ARMY_GROUND:
                        handle_count(caller, event, "army_ground", -1)
                    handle_count(caller, event, unit_count_name, -1)
                    handle_count(caller, event, "army_count", -1)
            elif type(event) is UnitTypeChangeEvent:
                unit = str(event.unit).split()[0]
                if event.unit_type_name in ARMY_UNITS:
                    unit_count_name = "_".join(["unit", event.unit_type_name, "count"])

                    caller.players[event.unit.owner.pid]["army_event"].append((event.frame, "*", unit))

                    handle_count(caller, event, unit_count_name, 1)

        def handle_tech_events(caller, event):
            if type(event) is UnitDoneEvent:
                unit = str(event.unit).split()[0]
                if unit in TECH_UNITS:
                    caller.players[event.unit.owner.pid]["tech_building"].append((event.frame, "+", unit))
            elif type(event) is UnitDiedEvent:
                unit = str(event.unit).split()[0]
                if unit in TECH_UNITS:
                    caller.players[event.unit.owner.pid]["tech_building"].append((event.frame, "-", unit))
            elif type(event) is UnitTypeChangeEvent:
                if event.unit_type_name in ["GreaterSpire", "LurkerDen"]:
                    caller.players[event.unit.owner.pid]["tech_building"].append((event.frame, "*", event.unit_type_name))

        def handle_upgrade_events(caller, event):
            if type(event) is UpgradeCompleteEvent and event.frame > 0:
                if not event.upgrade_type_name.startswith("Spray"):
                    caller.players[event.pid]["upgrades"].append((event.frame, event.upgrade_type_name))

        def handle_mineral_events(caller, event):
            if type(event) is PlayerStatsEvent:
                caller.players[event.pid]["minerals_available"].append((event.frame, event.minerals_current))
                caller.players[event.pid]["mineral_collection_rate"].append((event.frame, event.minerals_collection_rate,))
                caller.players[event.pid]["mineral_cost_active_forces"].append((event.frame, event.minerals_used_active_forces))
                mins_per_worker = 0 if event.workers_active_count == 0 else event.minerals_collection_rate / event.workers_active_count
                caller.players[event.pid]["mineral_per_worker_rate"].append((event.frame, mins_per_worker))
                caller.players[event.pid]["mineral_spend"].append((event.frame, event.minerals_used_current))
                caller.players[event.pid]["mineral_value_current_technology"].append((event.frame, event.minerals_used_current_technology))
                caller.players[event.pid]["mineral_value_current_army"].append((event.frame, event.minerals_used_current_army))
                caller.players[event.pid]["mineral_value_current_economic"].append((event.frame, event.minerals_used_current_economy))
                caller.players[event.pid]["mineral_queued"].append((event.frame, event.minerals_used_in_progress))
                caller.players[event.pid]["mineral_queued_technology"].append((event.frame, event.minerals_used_in_progress_technology))
                caller.players[event.pid]["mineral_queued_army"].append((event.frame, event.minerals_used_in_progress_army))
                caller.players[event.pid]["mineral_queued_economic"].append((event.frame, event.minerals_used_in_progress_economy))

        def handle_hotkeys_events(caller,event):
            if type(event) is GetControlGroupEvent:
                caller.players[event.pid]["hotkey_used"].append((event.frame, event.hotkey))
            if type(event) is AddToControlGroupEvent:
                caller.players[event.pid]["hotkey_add"].append((event.frame, event.hotkey))
            if type(event) is SetControlGroupEvent:
                caller.players[event.pid]["hotkey_set"].append((event.frame, event.hotkey))

# ======================================================================================================================
# Aggregate all of our event parsers for use by our ReplayData class
# ======================================================================================================================

        handlers = [handle_expansion_events, handle_worker_events, handle_supply_events, handle_mineral_events,
                    handle_vespene_events, handle_ground_events, handle_air_events, handle_tech_events, handle_upgrade_events,
                    handle_unit_events, handle_hotkeys_events]

# ======================================================================================================================
# ReplayData class to structure and process replay files
# ======================================================================================================================

        class ReplayData:
            __parsers__ = handlers

            @classmethod
            def parse_replay(cls, replay=None, replay_file=None, file_object=None):

                replay_data = ReplayData(replay_file)
                try:
                    # This is the engine that holds some required plugins for parsing
                    engine = sc2reader.engine.GameEngine(plugins=[ContextLoader(), APMTracker(), SelectionTracker(), PACAnalyzer()])

                    if replay:
                        pass
                    elif replay_file and not file_object:
                        # Then we are not using ObjectStorage for accessing replay files
                        replay = sc2reader.load_replay(replay_file, engine=engine)
                    elif file_object:
                        # We are using ObjectStorage to access replay files
                        replay = sc2reader.load_replay(file_object, engine=engine)
                    else:
                        pass

                    # Get the number of frames (one frame is 1/16 of a second)
                    replay_data.frames = replay.frames
                    # Gets the game mode (if available)
                    replay_data.game_mode = replay.real_type
                    # Gets the map hash (if we want to download the map, or do map-based analysis)
                    replay_data.map_hash = replay.map_hash

                    # Use the parsers to get data
                    for event in replay.events:
                        for parser in cls.__parsers__:
                            parser(replay_data, event)

                    # Check if there was a winner
                    if replay.winner is not None:
                        replay_data.winners = replay.winner.players
                        replay_data.losers = [p for p in replay.players if p not in replay.winner.players]
                    else:
                        replay_data.winners = []
                        replay_data.losers = []
                    # Check to see if expansion data is available
                    # replay_data.expansion = replay.expasion
                    return replay_data
                except:
                    # Print our error and return NoneType object
                    print_exc()
                    return None

            def as_dict(self):
                return {
                    "processed_on": datetime.utcnow().isoformat(),
                    "replay_name": self.replay,
                    "expansion": self.expansion,
                    "frames": self.frames,
                    "mode": self.game_mode,
                    "map": self.map_hash,
                    "matchup": "v".join(sorted([s.detail_data["race"][0].upper() for s in self.winners + self.losers])),
                    "winners": [(s.pid, s.name, s.detail_data['race']) for s in self.winners],
                    "losers": [(s.pid, s.name, s.detail_data['race']) for s in self.losers],
                    "stats_names": [k for k in self.players[1].keys()],
                    "stats": {player: data for player, data in self.players.items()}
                }

            def __init__(self, replay):
                self.players = defaultdict(lambda: defaultdict(list))
                self.replay = replay
                self.winners = []
                self.losers = []
                self.expansion = None

        replay_object = ReplayData.parse_replay(replay=replay)
        replay_dict = replay_object.as_dict()

# ======================================================================================================================
# Build the basic output from rep file. Here you will have to add names and assign numbers for your extra replays.
# ======================================================================================================================

# SONATA1
        playerNamesAndPids = {
            'glabII':'302','glabIII':'303','glabIV':'304','glabVI':'306','glabVII':'305',
            'glabVIII':'308','glabIX':'309','glabX': '310','GLabXI':'307','glabXII':'312',
            'glXIV':'314','glabXV':'315','glabXVI':'316','glabXVII':'317','glabXVIII':'318',
            'glabXIX':'319','glabXX':'320','glabXXI':'321','glabXXII':'322','glabXXIII':'323',
            'glabXXIV':'324','glabXXV':'325','glabXXVI':'326','glabXXVII':'327','glabXXVIII':'328',
            'glabXXIX':'329','glabXXX':'330','glabXXXII':'332','glabXXXIV':'334','glabXXXV':'335',
            'glabXXXVI':'336','glXXXVIII':'338','glabXXXIX':'339','GlabXLI':'341','glabXLII':'342',
            'glabXLIII':'343','glabXLV':'345','glabXLVI':'346','glabXLVII':'347','glabXLIX':'349',
            'glabL':'350','glabLI':'351','glabLII':'352','glabLIII':'353','glabLIV':'354',
            'glabLV':'355','glabLVI':'356',  'glabLVII':'357','glabLVIII':'358','glabLIX': '359',
            'glabLX':'360','glabLXI': '361','glabLXII':'362','glabLXIII':'363','glabLXIV':'364',
            'glabLXV':'365','glabLXVI':'366','glabLXVIII':'368','glabLXIX':'301','glabLXX':'370',
            'glabLXXIV': '344',
# SONATA2
            'glabCII':'3002','glabCIV':'3004','glabCV':'3005','glabCVI':'3006','glabCVIII':'3008',
            'glabCXI':'3011','glabCXII':'3012','glabCXIII':'3013','glabCXIV':'3014','glabCXV':'3015',
            'glabCXVI':'3016','GlabCXVII':'3017','glabCXVIII':'3018','glabCXX':'3020','glabCXXI':'3021',
            'glabCXXII':'3022','glabCXXIII':'3023','glabCXXIV':'3024','glabCXXV':'3025','glabCXXVI':'3026',
            'barcode':'1111', 'MAXPOWER':'2222'
        }

        # Main dict for storage of exported data
        output_basic = {}
        player_entity = ""
        opponent_entity = ""
        replay_data = copy.deepcopy(replay_object)

        # Identify the player
        # ==============================================================================================================
        output_basic['fileID'] = fh.name

        # Get the list of game Player filtered for Participants (Human and AI)
        entities_list = [i for i in replay.entity.items() if isinstance(i[1],sc2reader.objects.Participant)]

        if len(replay.humans) > 1:
            for elem in entities_list:
                if elem[1].name in [k for k in playerNamesAndPids]:
                    player_entity = elem[0]  # get the key number for player
                if elem[1].name not in [k for k in playerNamesAndPids]:
                    opponent_entity = elem[0]  # get the key number for opponent

        if len(replay.computers) > 0 or player_entity == '':  # if the game is against AI or player_entity was not found in PIDs list
            player_entity = replay.entity.items()[0][0]  # get the key number for player
            opponent_entity = replay.entity.items()[1][0]  # get the key number for opponent

        # Underneath is the basic structure used to encode variables into our output dictionary. Take some time to familiarize
        # yourself with it
        # ==============================================================================================================
        output_basic['playerName'] = replay.entity[player_entity].name.encode('utf-8')
        output_basic['playerType'] = "Human" if replay.entity[player_entity].is_human else "AI"

        # Basically it is output_basic['name of the variable'] = variable (usually in the form of replay.something)
        # ==============================================================================================================

        output_basic['opponentName'] = replay.entity[opponent_entity].name.encode('utf-8')
        output_basic['opponentType'] = "Human" if replay.entity[opponent_entity].is_human else "AI"

        # If the player's nickname can not be converted to PId, use original value
        # ==============================================================================================================
        if replay.entity[player_entity].name.encode('utf-8') in playerNamesAndPids:
            output_basic['participantId'] = playerNamesAndPids[replay.entity[player_entity].name.encode('utf-8')]
        else:
            output_basic['participantId'] = replay.entity[player_entity].name.encode('utf-8')

        # Check if match has a result
        # ==============================================================================================================
        if replay.entity[player_entity].result is not None:
            output_basic['matchResult'] = replay.entity[player_entity].result.encode('utf-8')
        else:
            output_basic['matchResult'] = "None".encode('utf-8')

        # APMs (action per minute)
        # ==============================================================================================================
        output_basic['playerAvgAPM'] = replay.entity[player_entity].avg_apm
        if len(replay.humans) > 1:
            output_basic['opponentAvgAPM'] = replay.entity[opponent_entity].avg_apm

        # Global match parameters
        # ==============================================================================================================
        output_basic['matchStartDateTime'] = replay.start_time.isoformat()
        output_basic['matchEndDateTime'] = replay.end_time.isoformat()
        output_basic['matchLengthRealTime'] = replay.game_length.seconds
        output_basic['matchLength'] = replay.game_length.seconds * 1.4
        output_basic['matchMapName'] = replay.map_name.encode('utf-8')

        # Check if match was set up with an AI opponent
        # ==============================================================================================================
        if len(replay.computers) > 0:
            output_basic['opponentDifficulty'] = replay.entity[opponent_entity].difficulty.encode('utf-8')
            output_basic['opponentRace'] = replay.entity[opponent_entity].play_race.encode('utf-8')
            output_basic['opponentBuild'] = replay.entity[opponent_entity].slot_data['ai_build']
            output_basic['opponentHandicap'] = replay.entity[opponent_entity].slot_data['handicap']
        else:
            output_basic['opponentRace'] = replay.entity[opponent_entity].play_race.encode('utf-8')

        # Spending Quotient
        # The first line underneath is redundant and used only for aesthetic reasons, can thus be discarded when
        # real data is going to be extracted
        # ==============================================================================================================
        output_basic['=============RESOURCES_PLAYER============='] = "=========================================="

        # Get Average Mineral Collection Rate
        output_basic['playerAverageMineralCollectionRate'] = sum(
            [pair[1] for pair in replay_object.players[player_entity]['mineral_collection_rate']]) / len(
            replay_object.players[player_entity]['mineral_collection_rate'])


        # Get Average Vespene Collection Rate
        output_basic['playerAverageVespeneCollectionRate'] = sum(
            [pair[1] for pair in replay_object.players[player_entity]['vespene_collection_rate']]) / len(
            replay_object.players[player_entity]['vespene_collection_rate'])



        # Calculate Average Resources Collection Rate (Minerals+Vespene) - ARCR
        output_basic['playerAverageResourcesCollectionRate'] = (output_basic['playerAverageMineralCollectionRate'] + output_basic[
            'playerAverageVespeneCollectionRate'])


        # Get Average Minerals Available
        output_basic['playerAverageMineralsAvailable'] = sum(
            [pair[1] for pair in replay_object.players[player_entity]['minerals_available']]) / len(
            replay_object.players[player_entity]['minerals_available'])


        # Get Average Vespene Available
        output_basic['playerAverageVespeneAvailable'] = sum(
            [pair[1] for pair in replay_object.players[player_entity]['vespene_available']]) / len(
            replay_object.players[player_entity]['vespene_available'])


        # Calculate Average Resources Available (Minerals+Vespene) - ARA
        output_basic['playerAverageResourcesAvailable'] = (output_basic['playerAverageMineralsAvailable'] + output_basic[
            'playerAverageVespeneAvailable'])



    #OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=OPPONENT=
        # The code underneath also gathers the spending data but instead doing it for the player, it does it for the
        # opponent. Take a look at the code beneath and notice what makes it different from the code from above.
        # ==============================================================================================================

        output_basic['============RESOURCES_OPPONENT============'] = "=========================================="
            # Get OPPONENT Average Mineral Collection Rate
        output_basic['opponentAverageMineralCollectionRate'] = sum(
            [pair[1] for pair in replay_object.players[opponent_entity]['mineral_collection_rate']]) / len(
            replay_object.players[opponent_entity]['mineral_collection_rate'])

        # Get OPPONENT Average Vespene Collection Rate
        output_basic['opponentAverageVespeneCollectionRate'] = sum(
            [pair[1] for pair in replay_object.players[opponent_entity]['vespene_collection_rate']]) / len(
            replay_object.players[opponent_entity]['vespene_collection_rate'])

        # Calculate OPPONENT Average Resources Collection Rate (Minerals+Vespene) - ARCR
        output_basic['opponentAverageResourcesCollectionRate'] = (
                    output_basic['opponentAverageMineralCollectionRate'] + output_basic[
                'opponentAverageVespeneCollectionRate'])

        # Get OPPONENT Average Minerals Available
        output_basic['opponentAverageMineralsAvailable'] = sum(
            [pair[1] for pair in replay_object.players[opponent_entity]['minerals_available']]) / len(
            replay_object.players[opponent_entity]['minerals_available'])

        # Get OPPONENT Average Vespene Available
        output_basic['opponentAverageVespeneAvailable'] = sum(
            [pair[1] for pair in replay_object.players[opponent_entity]['vespene_available']]) / len(
            replay_object.players[opponent_entity]['vespene_available'])

        # Calculate OPPONENT Average Resources Available (Minerals+Vespene) - ARA
        # ==============================================================================================================
        # ==============================================================================================================
        # ==============================================================================================================
        # EXERCISE: manipulate the code so that it will encode the 'opponentAverageResourcesAvailable' instead of
        # 'playerAverageResourcesAvailable' (hint: you have to change both the label and it's correspondent source.)

        output_basic['playerAverageResourcesAvailable'] = (
                    output_basic['playertAverageMineralsAvailable'] + output_basic[
                'playerAverageVespeneAvailable'])

        # ==============================================================================================================
        # ==============================================================================================================
        # ==============================================================================================================

        # Group hot keys usage
        output_basic['==============HOTKEYS_PLAYER=============='] = "=========================================="
        if len(replay_data.players) > 2:
            output_basic['playerHotkeysUsageTotal'] = len(replay_data.players[player_entity-1]['hotkey_used'])

            output_basic['playerHotkeysUsageIntensity'] = output_basic['playerHotkeysUsageTotal'] / output_basic['matchLength']

            output_basic['playerHotkeysSetaddTotal'] = len(replay_data.players[player_entity-1]['hotkey_add']) + len(
                replay_data.players[player_entity-1]['hotkey_set'])

            output_basic['playerHotkeysSetaddIntensity'] = output_basic['playerHotkeysSetaddTotal'] / output_basic['matchLength']

        # Group OPPONENT hot keys usage
        output_basic['============HOTKEYS_OPPONNENT============'] = "=========================================="
        if len(replay_data.players) > 2:
            output_basic['opponentHotkeysUsageTotal'] = len(replay_data.players[opponent_entity - 1]['hotkey_used'])

            output_basic['opponentHotkeysUsageIntensity'] = output_basic['opponentHotkeysUsageTotal'] / output_basic[
                'matchLength']
            # ==============================================================================================================
            # ==============================================================================================================
            # ==============================================================================================================
            # Fix this line: (when in doubt, ask)
            output_basic['playerHotkeysSetaddTotal'] = len(replay_data.players[player_entity - 1]['hotkey_add']) + len(
                replay_data.players[player_entity - 1]['hotkey_set'])
            # ==============================================================================================================
            # ==============================================================================================================
            # ==============================================================================================================

            output_basic['opponentHotkeysSetaddIntensity'] = output_basic['opponentHotkeysSetaddTotal'] / output_basic[
                'matchLength']

        # Data on the first attack move time
        output_basic['================FIRSTATTACK================'] = "=========================================="

        command_events_attack = [e for e in [i for i in replay.events if type(i) is sc2reader.events.game.TargetPointCommandEvent]
                                 if e.ability_name=='Attack']

        if len(command_events_attack) > 0:
            output_basic['playerFirstAttackMoveTime'] = command_events_attack[0].second
        else:
            output_basic['playerFirstAttackMoveTime'] = None

        # Data on PLAYER units and buildings
        output_basic['==========UNITS&BUILDINGS_PLAYER=========='] = "=========================================="
        # ==============================================================================================================
        output_basic['playerUnitsVariability'] = len(Counter(elem[2] for elem in replay_data.players[player_entity]['army_event']))

        player_supply_events = replay_data.players[player_entity]['supply_event']

        if len(player_supply_events) > 0:
            output_basic['playerFirstSupplyEventTime'] = player_supply_events[0][0]/16/1.4
        else:
            output_basic['playerFirstSupplyEventTime'] = None

        player_army_events = replay_data.players[player_entity]['army_event']

        if len(player_army_events) > 0:
            output_basic['playerFirstArmyEventTime'] = player_army_events[0][0]/16/1.4
        else:
            output_basic['playerFirstArmyEventTime'] = None

        player_army_events_destroy = [i for i in replay_data.players[player_entity]['army_event'] if i[1] == '-']

        if len(player_army_events_destroy) > 0:
            output_basic['playerFirstArmyLostTime'] = player_army_events_destroy[0][0]/16/1.4
        else:
            output_basic['playerFirstArmyLostTime'] = None


        # in vs AI reps opponent does not issue TargetPointCommands
        # The code here will add prices of the units as specified in the dictionaries above to the preset variables.

        army_events_create = [i for i in replay_data.players[player_entity]['army_event'] if i[1] == '+']

        output_basic['playerTotalArmySupplyCost'] = 0
        output_basic['playerTotalArmySupplyCostBasicGround'] = 0
        output_basic['playerTotalArmySupplyCostAdvancedGround'] = 0
        output_basic['playerTotalArmySupplyCostAdvancedAir'] = 0
        output_basic['playerTotalArmyUnits'] = len(army_events_create)
        output_basic['playerTotalArmyUnitsBasicGround'] = 0
        output_basic['playerTotalArmyUnitsAdvancedGround'] = 0
        output_basic['playerTotalArmyUnitsAdvancedAir'] = 0

        for unit in army_events_create:
            unit_name = unit[2]

            try: output_basic['playerTotalArmySupplyCost'] += ARMY_UNITS_COST[unit_name]
            except:
                output_basic['playerTotalArmySupplyCost'] += 0
                print(unit_name)

            # basic ground units
            if unit_name in ["Marine","Marauder","Reaper","Ghost",'Queen','Zergling','Baneling','Roach','Ravager','Zealot','Stalker','Sentry','Adept','HighTemplar','DarkTemplar']:
                output_basic['playerTotalArmyUnitsBasicGround'] += 1
                output_basic['playerTotalArmySupplyCostBasicGround'] += ARMY_UNITS_COST[unit_name]

            # advanced ground units
            if unit_name in ["Hellion","Hellbat","SiegeTank","Cyclone","WidowMine","Thor",'Hydralisk','Lurker','Infestor','SwarmHost','Ultralisk','Immortal','Colossus','Disruptor']:
                output_basic['playerTotalArmyUnitsAdvancedGround'] += 1
                output_basic['playerTotalArmySupplyCostAdvancedGround'] += ARMY_UNITS_COST[unit_name]

            # advanced air units
            if unit_name in ["Viking","Medivac","Liberator","Raven","Banshee","Battlecruiser",'Overseer','Mutalisk','Corruptor','BroodLord','Viper','Phoenix','VoidRay','Oracle','Carrier','Tempest']:
                output_basic['playerTotalArmyUnitsAdvancedAir'] += 1
                output_basic['playerTotalArmySupplyCostAdvancedAir'] += ARMY_UNITS_COST[unit_name]

        if output_basic['playerTotalArmyUnits'] > 0:
            output_basic['playerAverageArmySupplyCost'] = output_basic['playerTotalArmySupplyCost'] / output_basic['playerTotalArmyUnits']
        else:
            output_basic['playerAverageArmySupplyCost'] = 0

        if output_basic['playerTotalArmyUnitsBasicGround'] > 0:
            output_basic['playerAverageArmySupplyCostBasicGround'] = output_basic['playerTotalArmySupplyCostBasicGround'] / output_basic['playerTotalArmyUnitsBasicGround']
        else:
            output_basic['playerAverageArmySupplyCostBasicGround'] = 0

        if output_basic['playerTotalArmyUnitsAdvancedGround'] > 0:
            output_basic['playerAverageArmySupplyCostAdvancedGround'] = output_basic['playerTotalArmySupplyCostAdvancedGround'] / output_basic['playerTotalArmyUnitsAdvancedGround']
        else:
            output_basic['playerAverageArmySupplyCostAdvancedGround'] = 0

        if output_basic['playerTotalArmyUnitsAdvancedAir'] > 0:
            output_basic['playerAverageArmySupplyCostAdvancedAir'] = output_basic['playerTotalArmySupplyCostAdvancedAir'] / output_basic['playerTotalArmyUnitsAdvancedAir']
        else:
            output_basic['playerAverageArmySupplyCostAdvancedAir'] = 0

        #==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT==OPPONENT
        output_basic['=========UNITS&BUILDINGS_OPPONENT========='] = "=========================================="

        output_basic['opponentUnitsVariability'] = len(Counter(elem[2] for elem in replay_data.players[opponent_entity]['army_event']))

        opponent_supply_events = replay_data.players[opponent_entity]['supply_event']

        if len(opponent_supply_events) > 0:
            output_basic['opponentFirstSupplyEventTime'] = opponent_supply_events[0][0]/16/1.4
        else:
            output_basic['opponentFirstSupplyEventTime'] = None

        opponent_army_events = replay_data.players[opponent_entity]['army_event']

        if len(opponent_army_events) > 0:
            output_basic['opponentFirstArmyEventTime'] = opponent_army_events[0][0]/16/1.4
        else:
            output_basic['opponentFirstArmyEventTime'] = None

        opponent_army_events_destroy = [i for i in replay_data.players[opponent_entity]['army_event'] if i[1] == '-']

        if len(opponent_army_events_destroy) > 0:
            output_basic['opponentFirstArmyLostTime'] = opponent_army_events_destroy[0][0]/16/1.4
        else:
            output_basic['opponentFirstArmyLostTime'] = None

        army_events_create = [i for i in replay_data.players[opponent_entity]['army_event'] if i[1] == '+']

        output_basic['opponentTotalArmySupplyCost'] = 0
        output_basic['opponentTotalArmySupplyCostBasicGround'] = 0
        output_basic['opponentTotalArmySupplyCostAdvancedGround'] = 0
        output_basic['opponentTotalArmySupplyCostAdvancedAir'] = 0
        output_basic['opponentTotalArmyUnits'] = len(army_events_create)
        output_basic['opponentTotalArmyUnitsBasicGround'] = 0
        output_basic['opponentTotalArmyUnitsAdvancedGround'] = 0
        output_basic['opponentTotalArmyUnitsAdvancedAir'] = 0

        for unit in army_events_create:
            unit_name = unit[2]

            try: output_basic['opponentTotalArmySupplyCost'] += ARMY_UNITS_COST[unit_name]
            except:
                output_basic['opponentTotalArmySupplyCost'] += 0
                print(unit_name)

            # basic ground units
            if unit_name in ["Marine","Marauder","Reaper","Ghost",'Queen','Zergling','Baneling','Roach','Ravager','Zealot','Stalker','Sentry','Adept','HighTemplar','DarkTemplar']:
                output_basic['opponentTotalArmyUnitsBasicGround'] += 1
                output_basic['opponentTotalArmySupplyCostBasicGround'] += ARMY_UNITS_COST[unit_name]

            # advanced ground units
            if unit_name in ["Hellion","Hellbat","SiegeTank","Cyclone","WidowMine","Thor",'Hydralisk','Lurker','Infestor','SwarmHost','Ultralisk','Immortal','Colossus','Disruptor']:
                output_basic['opponentTotalArmyUnitsAdvancedGround'] += 1
                output_basic['opponentTotalArmySupplyCostAdvancedGround'] += ARMY_UNITS_COST[unit_name]

            # advanced air units
            if unit_name in ["Viking","Medivac","Liberator","Raven","Banshee","Battlecruiser",'Overseer','Mutalisk','Corruptor','BroodLord','Viper','Phoenix','VoidRay','Oracle','Carrier','Tempest']:
                output_basic['opponentTotalArmyUnitsAdvancedAir'] += 1
                output_basic['opponentTotalArmySupplyCostAdvancedAir'] += ARMY_UNITS_COST[unit_name]

        if output_basic['opponentTotalArmyUnits'] > 0:
            output_basic['opponentAverageArmySupplyCost'] = output_basic['opponentTotalArmySupplyCost'] / output_basic['opponentTotalArmyUnits']
        else:
            output_basic['opponentAverageArmySupplyCost'] = 0

        if output_basic['opponentTotalArmyUnitsBasicGround'] > 0:
            output_basic['opponentAverageArmySupplyCostBasicGround'] = output_basic['opponentTotalArmySupplyCostBasicGround'] / output_basic['opponentTotalArmyUnitsBasicGround']
        else:
            output_basic['opponentAverageArmySupplyCostBasicGround'] = 0

        if output_basic['opponentTotalArmyUnitsAdvancedGround'] > 0:
            output_basic['opponentAverageArmySupplyCostAdvancedGround'] = output_basic['opponentTotalArmySupplyCostAdvancedGround'] / output_basic['opponentTotalArmyUnitsAdvancedGround']
        else:
            output_basic['opponentAverageArmySupplyCostAdvancedGround'] = 0

        if output_basic['opponentTotalArmyUnitsAdvancedAir'] > 0:
            output_basic['opponentAverageArmySupplyCostAdvancedAir'] = output_basic['opponentTotalArmySupplyCostAdvancedAir'] / output_basic['opponentTotalArmyUnitsAdvancedAir']
        else:
            output_basic['opponentAverageArmySupplyCostAdvancedAir'] = 0


        # PACs Some additional metrics (Player action cycle)
        # ==============================================================================================================
        output_basic['==================PAC*PAC*=================='] = "=========================================="

        output_basic['PACsDispTreshold'] = replay.PACInfo.DispThreshold
        output_basic['PACsDurTreshold'] = replay.PACInfo.DurThreshold

        if hasattr(replay.entity[player_entity], "PACStats"):
            output_basic['playerPACsActionsPerPAC'] = replay.entity[player_entity].PACStats.app
            output_basic['playerPACsGapToNextPAC'] = replay.entity[player_entity].PACStats.gap
            output_basic['playerPACsActionLatency'] = replay.entity[player_entity].PACStats.pal
            output_basic['playerPACsPerMinute'] = replay.entity[player_entity].PACStats.ppm
        else:
            output_basic['playerPACsMissing'] = True

        if hasattr(replay.entity[opponent_entity], "PACStats"):
            output_basic['opponentPACsActionsPerPAC'] = replay.entity[player_entity].PACStats.app
            output_basic['opponentPACsGapToNextPAC'] = replay.entity[player_entity].PACStats.gap
            output_basic['opponentPACsActionLatency'] = replay.entity[player_entity].PACStats.pal
            output_basic['opponentPACsPerMinute'] = replay.entity[player_entity].PACStats.ppm
        else:
            output_basic['opponentPACsMissing'] = True

        pd.set_option("display.max_rows", None, "display.max_columns", None)


        # This is some dead code, don't touch it just in case
        # Record minute by minute
        # ==============================================================================================================
       # listMbmVars = []
       # minuteInFrames = 16 * 60
       #
       # for var in listMbmVars:
       #     minuteCounter = 0
       #     frameCounter = 0
       #     for frame, value in enumerate(var):
       #         sum = value[1]
       #         ++frameCounter
       #         if frameCounter > minuteInFrames:
       #             ++minuteCounter
       #             output_basic['supply_utilization_minute_'+minuteCounter] = sum / frameCounter
       #             frameCounter = 0

# ======================================================================================================================
# Download the ranking information
# This part of the code takes the url of the player's account site from the replay, downloads the site and
# parses it to extract information about the rank level of the players
# The function 'ranks' is so long because of the need to take into account both the situation in which both players
# are humans (x==2), and the situation when one of them is a computer (x==1).
# ======================================================================================================================

        # transforms the url to the account site into one that will take us straight to the rank data
        def url_update(x):
            txt = x.split("/")
            id = txt[6]
            url = f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{id}?locale=en_US"
            return url

        # extracts data from the site and adds it to the output_basic
        def ranks(x):
            if x==1:
                for player in replay.players:
                    try:
                        url = player.url
                        url = url_update(url)
                        with urllib.request.urlopen(url) as url:
                            data = json.loads(url.read().decode())
                            output_basic["===============PLAYER_RANKING==============="] = "=========================================="
                            output_basic["player1v1LeagueName"] = data["snapshot"]["seasonSnapshot"]["1v1"][
                                "leagueName"]
                            output_basic["playerRank"] = data["snapshot"]["seasonSnapshot"]["1v1"]["rank"]
                            output_basic["playerTotalRankGames"] = data["snapshot"]["seasonSnapshot"]["1v1"][
                                "totalGames"]
                            output_basic["playerTotalRankWins"] = data["snapshot"]["seasonSnapshot"]["1v1"]["totalWins"]
                            output_basic["===============PLAYER_CASUAL==============="] = "=========================================="
                            output_basic["playerTerranWins"] = data["career"]["terranWins"]
                            output_basic["playerZergWins"] = data["career"]["zergWins"]
                            output_basic["playerProtossWins"] = data["career"]["protossWins"]
                            output_basic["playerTotalGamesThisSeason"] = data["career"]["totalGamesThisSeason"]
                            output_basic["===============PLAYER_HISTORY==============="] = "=========================================="
                            output_basic["playerBestLeague"] = data["career"]["best1v1Finish"]["leagueName"]
                            output_basic["playerTimesBestLeague"] = data["career"]["best1v1Finish"]["timesAchieved"]
                            output_basic["playerTotalCareerGames"] = data["career"]["totalCareerGames"]
                    except:
                        print("bop") # bop
            elif x==2:
                for player in replay.players:
                    for elem in entities_list:
                        if elem[1].name in [k for k in playerNamesAndPids]: # if you will add both the player's and opponent's name
                            url = player.url                                # to the dictionary with pids (somewhere above)
                            url = url_update(url)                           # then this code won't work, so don't do it
                            with urllib.request.urlopen(url) as url:
                                data = json.loads(url.read().decode())
                                output_basic["==============PLAYER_RANKING==============="] = "=========================================="
                                output_basic["player1v1LeagueName"] = data["snapshot"]["seasonSnapshot"]["1v1"][
                                    "leagueName"]
                                output_basic["playerRank"] = data["snapshot"]["seasonSnapshot"]["1v1"]["rank"]
                                output_basic["playerTotalRankGames"] = data["snapshot"]["seasonSnapshot"]["1v1"]["totalGames"]
                                output_basic["playerTotalRankWins"] = data["snapshot"]["seasonSnapshot"]["1v1"]["totalWins"]
                                output_basic["===============PLAYER_CASUAL==============="] = "=========================================="
                                output_basic["playerTerranWins"] = data["career"]["terranWins"]
                                output_basic["playerZergWins"] = data["career"]["zergWins"]
                                output_basic["playerProtossWins"] = data["career"]["protossWins"]
                                output_basic["playerTotalGamesThisSeason"] = data["career"]["totalGamesThisSeason"]
                                output_basic["===============PLAYER_HISTORY=============="] = "=========================================="
                                output_basic["playerBestLeague"] = data["career"]["best1v1Finish"]["leagueName"]
                                output_basic["playerTimesBestLeague"] = data["career"]["best1v1Finish"]["timesAchieved"]
                                output_basic["playerTotalCareerGames"] = data["career"]["totalCareerGames"]
                        if elem[1].name not in [k for k in playerNamesAndPids]:
                            url = player.url
                            url = url_update(url)
                            with urllib.request.urlopen(url) as url:
                                data = json.loads(url.read().decode())
                                output_basic["=============OPPONENT_RANKING============="] = "=========================================="
                                output_basic["oppponent1v1LeagueName"] = data["snapshot"]["seasonSnapshot"]["1v1"]["leagueName"]
                                output_basic["oppponentRank"] = data["snapshot"]["seasonSnapshot"]["1v1"]["rank"]
                                output_basic["oppponentTotalRankGames"] = data["snapshot"]["seasonSnapshot"]["1v1"]["totalGames"]
                                output_basic["oppponentTotalRankWins"] = data["snapshot"]["seasonSnapshot"]["1v1"]["totalWins"]
                                output_basic["==============OPPONENT_CASUAL============="] = "=========================================="
                                output_basic["oppponentTerranWins"] = data["career"]["terranWins"]
                                output_basic["oppponentZergWins"] = data["career"]["zergWins"]
                                output_basic["oppponentProtossWins"] = data["career"]["protossWins"]
                                output_basic["oppponentTotalGamesThisSeason"] = data["career"]["totalGamesThisSeason"]
                                output_basic["==============OPPONENT_HISTORY============="] = "=========================================="
                                output_basic["oppponentBestLeague"] = data["career"]["best1v1Finish"]["leagueName"]
                                output_basic["oppponentTimesBestLeague"] = data["career"]["best1v1Finish"]["timesAchieved"]
                                output_basic["oppponentTotalCareerGames"] = data["career"]["totalCareerGames"]

        ranks(len(replay.humans)) #calls the function above with the number of players as the input variable


# ======================================================================================================================
# Prepare the file - Here you will have to update where you want your results to be stored (save_path) as well as
# in what format. Right now it is set to html for the debugging sake but it will probably have to be changed eventually
# you can find ways to save dataframes into different formats online.
# ======================================================================================================================
        save_path = "/Users/hubertplisiecki/PycharmProjects/untitled/Dane"
        df = DataFrame(list(output_basic.items()), columns=['column1', 'column2'])
        df_html = df.to_html()
        with open(os.path.join(save_path, f'{output_basic["playerName"]}.html'), 'w') as f:
            print(output_basic["playerName"])
            f.write(df_html)


print (file_search_stats)
print (file_search_duplicates_timestamps)
print ("All went well")

# EOF

