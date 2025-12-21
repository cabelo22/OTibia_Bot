import random

import numpy as np
from PyQt5.QtCore import QThread, QMutex, QMutexLocker
from pytesseract import Output

import Addresses
from Addresses import coordinates_x, coordinates_y, screen_width, screen_height, screen_x, screen_y, walker_Lock, \
    battle_x, battle_y
from Functions.GeneralFunctions import load_items_images
from Functions.MemoryFunctions import *
from Functions.GeneralFunctions import WindowCapture, merge_close_points
from Functions.KeyboardFunctions import press_hotkey, chase_monster, stay_diagonal, chaseDiagonal_monster
from Functions.MouseFunctions import manage_collect, mouse_function
from Looting.LootingThread import LootThread
from Functions.KeyboardFunctions import walk
from Functions.PathfindingFunctions import expand_waypoints, calculate_path_astar
import cv2 as cv
import pytesseract


class TargetThread(QThread):

    def __init__(self, targets, loot_state, attack_key, loot_table=None, blacklist_tiles=None):
        super().__init__()
        self.running = True
        self.targets = targets
        self.attack_key = attack_key + 1
        self.loot_state = loot_state
        self.state_lock = QMutex()
        self.loot_table = loot_table
        self.looting_thread = None
        self.discovered_obstacles = set()

    def __init__(self, targets, loot_state, attack_key, loot_table=None, blacklist_tiles=None):
        super().__init__()
        self.running = True
        self.targets = targets
        self.attack_key = attack_key + 1
        self.loot_state = loot_state
        self.state_lock = QMutex()
        self.loot_table = loot_table
        self.looting_thread = None
        self.discovered_obstacles = set()
        self.last_target_pos = None
        self.blacklist_tiles = blacklist_tiles if blacklist_tiles else set()

    def run(self):
        my_x, my_y, my_z = read_my_wpt()
        previous_pos = (my_x, my_y, my_z)
        stuck_timer = 0
        current_target_name = ""
        while self.running:
            QThread.msleep(random.randint(70, 100))
            try:
                open_corpse = False
                target_id = read_targeting_status()
                if target_id == 0:
                    self.discovered_obstacles.clear()
                    stuck_timer = 0
                    self.last_target_pos = None

                    if self.attack_key == 13:  # OCR Battle List Mode
                        self.scan_and_click_battle_list_ocr()
                    else:
                        press_hotkey(self.attack_key)

                    QThread.msleep(random.randint(100, 150))
                    target_id = read_targeting_status()
                    if target_id == 0:
                        if walker_Lock.locked():
                            walker_Lock.release()
                else:
                    target_x, target_y, target_z, target_name, target_hp = read_target_info()

                    if any(target['Name'] == target_name or target['Name'] == '*' for target in self.targets):
                        if any(target['Name'] == target_name for target in self.targets):
                            target_index = next(
                                i for i, target in enumerate(self.targets) if target['Name'] == target_name)
                        else:
                            target_index = 0
                        target_data = self.targets[target_index]
                        last_hp = target_hp
                        hp_unchanged_timer = 0
                        while read_targeting_status() != 0:
                            target_current_x, target_current_y, target_current_z, target_name, target_hp = read_target_info()
                            if target_z == target_current_z:
                                target_x = target_current_x
                                target_y = target_current_y
                                target_z = target_current_z
                            sleep_value = random.randint(40, 80)
                            x, y, z = read_my_wpt()
                            dist_x = abs(x - target_x)
                            dist_y = abs(y - target_y)
                            if (target_data['Dist'] >= dist_x and target_data['Dist'] >= dist_y) or target_data[
                                'Dist'] == 0:
                                if self.loot_table:
                                    open_corpse = True
                                if not walker_Lock.locked():
                                    walker_Lock.acquire()
                                if dist_x > 1 or dist_y > 1:
                                    if target_data['Stance'] == 1:  # Chase
                                        # Filter blacklist for current Z level and merge with discovered obstacles
                                        blacklist_2d = {(bx, by) for bx, by, bz in self.blacklist_tiles if bz == z}
                                        all_obstacles = self.discovered_obstacles | blacklist_2d
                                        path = calculate_path_astar(x, y, target_x, target_y, all_obstacles)
                                        if path:
                                            next_step = path[0]
                                            self.last_target_pos = (x + next_step[0], y + next_step[1])
                                            walk(0, x, y, z, x + next_step[0], y + next_step[1], z)
                                            QThread.msleep(random.randint(100, 200))
                                            # Read current position after walk for accurate stuck detection
                                            my_x, my_y, my_z = read_my_wpt()

                                            # Stuck detection
                                            if (my_x, my_y, my_z) == previous_pos:
                                                stuck_timer += sleep_value  # Increment by actual sleep time
                                            else:
                                                previous_pos = (my_x, my_y, my_z)
                                                stuck_timer = 0

                                            if stuck_timer > 400:  # Stuck for 0.4 second
                                                if self.last_target_pos:
                                                    self.discovered_obstacles.add(self.last_target_pos)
                                                    stuck_timer = 0
                                                    print(f"Stuck! Added obstacle at {self.last_target_pos}")
                                                    self.last_target_pos = None
                            else:
                                if walker_Lock.locked():
                                    walker_Lock.release()
                                press_hotkey(self.attack_key)
                                QThread.msleep(random.randint(100, 150))

                            QThread.msleep(sleep_value)
                            hp_unchanged_timer += sleep_value
                        x, y, z = read_my_wpt()
                        x = target_x - x
                        y = target_y - y
                        corpse_x = coordinates_x[0] + x * Addresses.square_size
                        corpse_y = coordinates_y[0] + y * Addresses.square_size
                        if open_corpse:
                            QThread.msleep(random.randint(400, 500))
                            if self.looting_thread and self.looting_thread.isRunning():
                                self.looting_thread.stop()
                                self.looting_thread.wait(10)
                            mouse_function(corpse_x, corpse_y, option=1)
                            QThread.msleep(random.randint(300, 500))  # Small delay to allow container to open

                            # Start new looting thread if loot table is available
                            if self.loot_table:
                                self.looting_thread = LootThread(self.loot_table, self.loot_state, one_shot=True)
                                self.looting_thread.start()
                        if 'Skin' in target_data and target_data['Skin'] > 0:
                            press_hotkey(target_data['Skin'])
                            QThread.msleep(random.randint(10, 50))
                            mouse_function(corpse_x, corpse_y, option=2)
                            QThread.msleep(random.randint(150, 250))

                    else:
                        if walker_Lock.locked():
                            walker_Lock.release()
                        press_hotkey(self.attack_key)
                        QThread.msleep(random.randint(100, 150))

            except Exception as e:
                print("Exception : ", e)

    def update_states(self, option, state):
        with QMutexLocker(self.state_lock):
            if option == 0:
                self.loot_state = state

    def scan_and_click_battle_list_ocr(self):
        try:
            bx, by = Addresses.battle_x[0], Addresses.battle_y[0]
            bw, bh = Addresses.screen_width[1], Addresses.screen_height[1]

            if bh <= by or bw <= bx:
                return

            width = bw - bx
            height = bh - by

            # Capture Battle List region
            capture = WindowCapture(width, height, bx, by)
            screenshot = capture.get_screenshot()

            # Preprocess for OCR
            gray = cv.cvtColor(screenshot, cv.COLOR_BGR2GRAY)
            # Thresholding to isolate text
            _, thresh = cv.threshold(gray, 150, 255, cv.THRESH_BINARY_INV)

            # Run OCR to get strings and their coordinates
            data = pytesseract.image_to_data(thresh, output_type=Output.DICT)

            n_boxes = len(data['text'])

            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:
                    continue

                # Check if this text matches any of our targets
                should_click = False
                for target in self.targets:
                    # Case insensitive check or wildcard
                    if target['Name'] == '*' or target['Name'].upper() == text.upper():
                        should_click = True
                        break

                if should_click:
                    # Calculate center of the text box
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]

                    click_x = bx + x + (w // 2)
                    click_y = by + y + (h // 2) - Addresses.TITLE_BAR_OFFSET

                    print(f"OCR Match! Clicking '{text}' at ({click_x}, {click_y})")
                    mouse_function(click_x, click_y, option=2)
                    return  # Exit after one click to let the targeting status update

        except Exception as e:
            print(f"Error in scan_and_click_battle_list_ocr: {e}")

    def stop(self):
        self.running = False
        if self.looting_thread:
            self.looting_thread.stop()
            self.looting_thread.wait()

