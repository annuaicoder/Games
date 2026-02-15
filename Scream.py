from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

app = Ursina(title='SCREAM - Psychological Horror', borderless=False)
window.fullscreen = False
window.color = color.rgb(5, 5, 10)
window.fps_counter.enabled = False

# ============================================================================
# GAME STATE
# ============================================================================
game_over = False
game_won = False
sanity = 100  # Player's sanity level - decreases when ghost is near
ghost_seen_timer = 0
flicker_timer = 0
ambient_fear = 0
heartbeat_intensity = 0

# ============================================================================
# LOAD TEXTURES FROM PARENT DIRECTORY
# ============================================================================
wall_texture = load_texture('../../wall_converted.png')
ghost_texture = load_texture('../../ghost_converted.png')
bed_texture = load_texture('../../bed_converted.png')

# ============================================================================
# AUDIO SETUP
# ============================================================================
# Heavy breathing background audio - loops continuously
breathing_audio = Audio('../../freesound_community-heavy-breathing-14431.mp3', loop=True, autoplay=True, volume=0.4)

# Scream sound for jumpscare - played when ghost catches player
scream_audio = Audio('../../scream.mp3', loop=False, autoplay=False, volume=1.0)

# ============================================================================
# LIGHTING SYSTEM WITH FLICKERING
# ============================================================================
class FlickeringLight(Entity):
    def __init__(self, position, intensity=1.0, flicker_speed=0.1, **kwargs):
        super().__init__(**kwargs)
        self.light = PointLight(parent=self, position=position, color=color.rgb(255, 200, 150))
        self.base_intensity = intensity
        self.flicker_speed = flicker_speed
        self.flicker_timer = random.random() * 10
        self.is_on = True
        self.malfunction_chance = 0.02
        self.off_duration = 0
        
        # Visual bulb representation
        self.bulb = Entity(
            parent=self,
            model='sphere',
            scale=0.3,
            position=position,
            color=color.yellow,
            unlit=True
        )
    
    def update(self):
        global ambient_fear
        self.flicker_timer += time.dt
        
        # Random malfunction - light goes out temporarily
        if self.is_on and random.random() < self.malfunction_chance * (1 + ambient_fear * 0.5):
            self.is_on = False
            self.off_duration = random.uniform(0.1, 2.0)
        
        if not self.is_on:
            self.off_duration -= time.dt
            if self.off_duration <= 0:
                self.is_on = True
        
        # Flickering effect
        if self.is_on:
            flicker = math.sin(self.flicker_timer * 20) * 0.3 + random.uniform(-0.1, 0.1)
            intensity = max(0.2, self.base_intensity + flicker)
            self.light.color = color.rgb(
                int(255 * intensity),
                int(200 * intensity),
                int(150 * intensity)
            )
            self.bulb.color = color.rgb(255, 255, 200)
            self.bulb.scale = 0.3 + flicker * 0.1
        else:
            self.light.color = color.rgb(20, 15, 10)
            self.bulb.color = color.rgb(50, 40, 30)
            self.bulb.scale = 0.2

lights = []

# ============================================================================
# HOUSE STRUCTURE - MULTIPLE ROOMS
# ============================================================================
house_width = 60
house_depth = 60
wall_height = 8
wall_thickness = 0.5

# Floor
floor = Entity(
    model='plane',
    scale=(house_width, 1, house_depth),
    texture='white_cube',
    texture_scale=(20, 20),
    color=color.rgb(30, 25, 20),
    collider='box',
    position=(0, 0, 0)
)

# Ceiling
ceiling = Entity(
    model='plane',
    scale=(house_width, 1, house_depth),
    texture='white_cube',
    texture_scale=(20, 20),
    color=color.rgb(20, 18, 15),
    position=(0, wall_height, 0),
    rotation=(180, 0, 0)
)

def create_wall(pos, scale, scary=False):
    """Create a wall with scary texture"""
    wall = Entity(
        model='cube',
        position=pos,
        scale=scale,
        texture=wall_texture if scary else 'white_cube',
        texture_scale=(scale[0]/2, scale[1]/2) if scary else (1, 1),
        color=color.rgb(60, 50, 45) if not scary else color.rgb(80, 70, 65),
        collider='box'
    )
    return wall

# Outer walls with scary texture
walls = []
# North wall
walls.append(create_wall((0, wall_height/2, house_depth/2), (house_width, wall_height, wall_thickness), scary=True))
# South wall
walls.append(create_wall((0, wall_height/2, -house_depth/2), (house_width, wall_height, wall_thickness), scary=True))
# East wall
walls.append(create_wall((house_width/2, wall_height/2, 0), (wall_thickness, wall_height, house_depth), scary=True))
# West wall
walls.append(create_wall((-house_width/2, wall_height/2, 0), (wall_thickness, wall_height, house_depth), scary=True))

# ============================================================================
# ROOM LAYOUT - Creating multiple interconnected rooms
# ============================================================================
room_walls = []

# Room 1: Entrance Hall (South-West)
room_walls.append(create_wall((-15, wall_height/2, -10), (wall_thickness, wall_height, 20), scary=True))
room_walls.append(create_wall((-22.5, wall_height/2, 0), (15, wall_height, wall_thickness), scary=True))

# Room 2: Living Room (South-East)
room_walls.append(create_wall((10, wall_height/2, -15), (wall_thickness, wall_height, 10), scary=True))
room_walls.append(create_wall((17.5, wall_height/2, -10), (15, wall_height, wall_thickness), scary=True))

# Room 3: Kitchen (North-West)
room_walls.append(create_wall((-10, wall_height/2, 15), (20, wall_height, wall_thickness), scary=True))
room_walls.append(create_wall((-20, wall_height/2, 22.5), (wall_thickness, wall_height, 15), scary=True))

# Room 4: Bedroom (North-East) - This is where the bed is
room_walls.append(create_wall((15, wall_height/2, 10), (wall_thickness, wall_height, 20), scary=True))
room_walls.append(create_wall((22.5, wall_height/2, 20), (15, wall_height, wall_thickness), scary=True))

# Room 5: Bathroom (Center-North)
room_walls.append(create_wall((0, wall_height/2, 20), (10, wall_height, wall_thickness), scary=True))
room_walls.append(create_wall((5, wall_height/2, 25), (wall_thickness, wall_height, 10), scary=True))

# Room 6: Basement Stairs area (Center)
room_walls.append(create_wall((0, wall_height/2, 5), (8, wall_height, wall_thickness), scary=True))
room_walls.append(create_wall((-4, wall_height/2, 0), (wall_thickness, wall_height, 10), scary=True))

# Long Hallway
room_walls.append(create_wall((5, wall_height/2, -5), (wall_thickness, wall_height, 30), scary=True))

# ============================================================================
# BED IN BEDROOM - Using bed.png texture
# ============================================================================
bed = Entity(
    model='cube',
    position=(22, 0.5, 22),
    scale=(4, 1, 6),
    texture=bed_texture,
    texture_scale=(1, 1),
    collider='box'
)

# Bed frame
bed_headboard = Entity(
    model='cube',
    position=(22, 1.5, 24.5),
    scale=(4, 2, 0.3),
    texture=bed_texture,
    color=color.rgb(80, 60, 40)
)

# Pillow
pillow = Entity(
    model='cube',
    position=(22, 1.1, 23.5),
    scale=(2, 0.3, 1),
    color=color.rgb(200, 200, 200)
)

# ============================================================================
# CREEPY FURNITURE AND OBJECTS
# ============================================================================
# Old chairs
for pos in [(-20, 0.5, -20), (-18, 0.5, -22), (18, 0.5, -18)]:
    Entity(model='cube', position=pos, scale=(1, 1, 1), color=color.rgb(60, 40, 30), collider='box')

# Creepy paintings on walls (using wall texture for horror effect)
paintings = []
painting_positions = [
    ((-29.5, 4, -10), (0.1, 3, 2)),
    ((-29.5, 4, 10), (0.1, 3, 2)),
    ((29.5, 4, -10), (0.1, 3, 2)),
    ((0, 4, 29.5), (3, 2, 0.1)),
]
for pos, scale in painting_positions:
    p = Entity(
        model='cube',
        position=pos,
        scale=scale,
        texture=wall_texture,
        color=color.rgb(100, 80, 70)
    )
    paintings.append(p)

# Broken mirror
mirror = Entity(
    model='cube',
    position=(10, 4, -29.5),
    scale=(4, 3, 0.1),
    color=color.rgb(150, 150, 160),
    collider='box'
)

# ============================================================================
# FLICKERING LIGHTS PLACEMENT
# ============================================================================
light_positions = [
    (-20, 7, -20),  # Entrance
    (20, 7, -20),   # Living room
    (-20, 7, 20),   # Kitchen
    (22, 7, 22),    # Bedroom
    (0, 7, 22),     # Bathroom
    (0, 7, 0),      # Center
    (-10, 7, -10),  # Hallway 1
    (10, 7, 10),    # Hallway 2
]

for pos in light_positions:
    light = FlickeringLight(position=pos, intensity=0.8, flicker_speed=random.uniform(0.05, 0.2))
    lights.append(light)

# Main ambient light (very dim)
ambient = AmbientLight(color=color.rgb(15, 12, 10))

# ============================================================================
# GHOST ENTITY - The main threat
# ============================================================================
class Ghost(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='quad',
            texture=ghost_texture,
            scale=(3, 4),
            billboard=True,
            position=(20, 2, 20),
            collider='sphere',
            **kwargs
        )
        self.speed = 2.0
        self.chase_speed = 4.5
        self.is_chasing = False
        self.patrol_points = [
            Vec3(-20, 2, -20),
            Vec3(20, 2, -20),
            Vec3(20, 2, 20),
            Vec3(-20, 2, 20),
            Vec3(0, 2, 0),
            Vec3(-10, 2, 15),
            Vec3(15, 2, -10),
        ]
        self.current_patrol = 0
        self.detection_range = 15
        self.kill_range = 1.5
        self.visible = True
        self.teleport_timer = 0
        self.teleport_interval = random.uniform(8, 15)
        self.alpha = 0.9
        self.last_seen_player_pos = None
        self.aggression = 0  # Increases over time
        
    def update(self):
        global game_over, sanity, ghost_seen_timer, ambient_fear, heartbeat_intensity
        
        if game_over or game_won:
            return
            
        player_distance = distance(self.position, player.position)
        
        # Increase aggression over time
        self.aggression += time.dt * 0.01
        
        # Detection logic
        if player_distance < self.detection_range:
            # Check line of sight (simplified)
            self.is_chasing = True
            self.last_seen_player_pos = player.position
            ghost_seen_timer += time.dt
            
            # Decrease sanity when ghost is visible and close
            sanity_drain = (self.detection_range - player_distance) * 0.5 * time.dt
            sanity = max(0, sanity - sanity_drain)
            
            # Increase ambient fear
            ambient_fear = min(1, ambient_fear + time.dt * 0.1)
            heartbeat_intensity = min(1, (self.detection_range - player_distance) / self.detection_range)
        else:
            self.is_chasing = False
            ghost_seen_timer = max(0, ghost_seen_timer - time.dt * 0.5)
            ambient_fear = max(0, ambient_fear - time.dt * 0.05)
            heartbeat_intensity = max(0, heartbeat_intensity - time.dt * 0.3)
        
        # Movement
        if self.is_chasing:
            direction = (player.position - self.position).normalized()
            move_speed = self.chase_speed + self.aggression
            self.position += direction * move_speed * time.dt
            self.position.y = 2  # Keep ghost at proper height
        else:
            # Patrol behavior
            target = self.patrol_points[self.current_patrol]
            direction = (target - self.position).normalized()
            self.position += direction * self.speed * time.dt
            self.position.y = 2
            
            if distance(self.position, target) < 2:
                self.current_patrol = (self.current_patrol + 1) % len(self.patrol_points)
        
        # Random teleportation (psychological horror element)
        self.teleport_timer += time.dt
        if self.teleport_timer > self.teleport_interval:
            self.teleport_timer = 0
            self.teleport_interval = random.uniform(5, 12) - self.aggression
            # Teleport to a random location, sometimes closer to player
            if random.random() < 0.3 + self.aggression * 0.1:
                # Teleport near player (scary!)
                angle = random.uniform(0, 360)
                dist = random.uniform(8, 15)
                new_x = player.position.x + math.cos(math.radians(angle)) * dist
                new_z = player.position.z + math.sin(math.radians(angle)) * dist
                new_x = max(-28, min(28, new_x))
                new_z = max(-28, min(28, new_z))
                self.position = Vec3(new_x, 2, new_z)
            else:
                # Random teleport
                self.position = random.choice(self.patrol_points)
        
        # Ghost visual effects
        self.alpha = 0.7 + math.sin(time.time() * 3) * 0.2
        self.color = color.rgba(255, 255, 255, int(self.alpha * 255))
        
        # Kill player if too close
        if player_distance < self.kill_range:
            trigger_death()

ghost = Ghost()

# ============================================================================
# PLAYER SETUP
# ============================================================================
player = FirstPersonController(
    position=(-25, 2, -25),
    speed=5,
    mouse_sensitivity=Vec2(50, 50)
)
player.cursor.visible = False
player.gravity = 1

# Sprint functionality
sprint_speed = 8
normal_speed = 5
stamina = 100
stamina_regen = 15
stamina_drain = 25

# ============================================================================
# UI ELEMENTS
# ============================================================================
# Sanity meter
sanity_bar_bg = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.3, 0.03),
    position=(-0.6, 0.45),
    color=color.rgb(40, 0, 0)
)
sanity_bar = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.3, 0.025),
    position=(-0.6, 0.45),
    color=color.rgb(180, 50, 50),
    origin=(-0.5, 0)
)
sanity_text = Text(
    text='SANITY',
    parent=camera.ui,
    position=(-0.75, 0.47),
    scale=0.8,
    color=color.rgb(200, 100, 100)
)

# Stamina bar
stamina_bar_bg = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.3, 0.02),
    position=(-0.6, 0.40),
    color=color.rgb(0, 30, 0)
)
stamina_bar = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.3, 0.015),
    position=(-0.6, 0.40),
    color=color.rgb(50, 180, 50),
    origin=(-0.5, 0)
)

# Warning text (appears when ghost is near)
warning_text = Text(
    text='',
    parent=camera.ui,
    position=(0, 0.3),
    origin=(0, 0),
    scale=2,
    color=color.red
)

# Game title
title_text = Text(
    text='S C R E A M',
    parent=camera.ui,
    position=(0, 0.4),
    origin=(0, 0),
    scale=3,
    color=color.rgb(150, 0, 0)
)
invoke(setattr, title_text, 'enabled', False, delay=3)

# Instructions
instructions = Text(
    text='WASD - Move | SHIFT - Sprint | Avoid the Ghost | Find the Exit',
    parent=camera.ui,
    position=(0, -0.45),
    origin=(0, 0),
    scale=1,
    color=color.rgb(100, 100, 100)
)

# Vignette effect for horror atmosphere
vignette = Entity(
    parent=camera.ui,
    model='quad',
    scale=(2, 1),
    color=color.rgba(0, 0, 0, 100),
    z=10
)

# Screen flash for scares
screen_flash = Entity(
    parent=camera.ui,
    model='quad',
    scale=(2, 1),
    color=color.rgba(255, 0, 0, 0),
    z=5
)

# ============================================================================
# EXIT DOOR - Goal of the game
# ============================================================================
exit_door = Entity(
    model='cube',
    position=(-29.5, 2, 0),
    scale=(0.5, 4, 3),
    color=color.rgb(100, 70, 40),
    collider='box'
)
exit_sign = Text(
    text='EXIT',
    parent=exit_door,
    position=(0.3, 0.8, 0),
    scale=15,
    color=color.green,
    billboard=True
)

# ============================================================================
# GAME FUNCTIONS
# ============================================================================
def trigger_death():
    global game_over
    if game_over:
        return
    game_over = True
    player.enabled = False
    
    # Stop breathing and play scream jumpscare
    breathing_audio.stop()
    scream_audio.play()
    
    # JUMPSCARE - Ghost face fills screen
    jumpscare = Entity(
        parent=camera.ui,
        model='quad',
        texture=ghost_texture,
        scale=(1.5, 1.5),
        position=(0, 0),
        z=0
    )
    
    # Flash red screen rapidly for jumpscare effect
    for i in range(5):
        invoke(setattr, jumpscare, 'color', color.red, delay=i*0.1)
        invoke(setattr, jumpscare, 'color', color.white, delay=i*0.1 + 0.05)
    
    # Remove jumpscare after a moment and show death screen
    invoke(destroy, jumpscare, delay=1.5)
    
    # Death screen (delayed to show after jumpscare)
    invoke(show_death_screen, delay=1.5)

def show_death_screen():
    death_screen = Entity(
        parent=camera.ui,
        model='quad',
        scale=(2, 1),
        color=color.rgba(100, 0, 0, 200),
        z=1
    )
    death_text = Text(
        text='YOU DIED',
        parent=camera.ui,
        position=(0, 0.1),
        origin=(0, 0),
        scale=5,
        color=color.white
    )
    restart_text = Text(
        text='Press R to Restart',
        parent=camera.ui,
        position=(0, -0.1),
        origin=(0, 0),
        scale=2,
        color=color.rgb(200, 200, 200)
    )

def trigger_win():
    global game_won
    if game_won:
        return
    game_won = True
    player.enabled = False
    
    # Win screen
    win_screen = Entity(
        parent=camera.ui,
        model='quad',
        scale=(2, 1),
        color=color.rgba(0, 50, 0, 200),
        z=1
    )
    win_text = Text(
        text='YOU ESCAPED!',
        parent=camera.ui,
        position=(0, 0.1),
        origin=(0, 0),
        scale=4,
        color=color.white
    )
    score_text = Text(
        text=f'Sanity Remaining: {int(sanity)}%',
        parent=camera.ui,
        position=(0, -0.1),
        origin=(0, 0),
        scale=2,
        color=color.rgb(200, 200, 200)
    )

def restart_game():
    global game_over, game_won, sanity, stamina, ambient_fear
    game_over = False
    game_won = False
    sanity = 100
    stamina = 100
    ambient_fear = 0
    
    # Reset positions
    player.position = Vec3(-25, 2, -25)
    player.enabled = True
    ghost.position = Vec3(20, 2, 20)
    ghost.aggression = 0
    
    # Restart breathing audio
    scream_audio.stop()
    breathing_audio.play()
    
    # Clear UI elements
    for entity in camera.ui.children:
        if hasattr(entity, 'text') and entity.text in ['YOU DIED', 'YOU ESCAPED!', 'Press R to Restart']:
            destroy(entity)

# ============================================================================
# INPUT HANDLING
# ============================================================================
def input(key):
    if key == 'r' and (game_over or game_won):
        restart_game()
    if key == 'escape':
        application.quit()

# ============================================================================
# MAIN UPDATE LOOP
# ============================================================================
def update():
    global sanity, stamina, flicker_timer, ambient_fear
    
    if game_over or game_won:
        return
    
    # Sprint mechanics
    if held_keys['shift'] and stamina > 0:
        player.speed = sprint_speed
        stamina = max(0, stamina - stamina_drain * time.dt)
    else:
        player.speed = normal_speed
        stamina = min(100, stamina + stamina_regen * time.dt)
    
    # Update UI
    sanity_bar.scale_x = 0.3 * (sanity / 100)
    stamina_bar.scale_x = 0.3 * (stamina / 100)
    
    # Sanity effects
    if sanity < 50:
        # Screen distortion at low sanity
        vignette.color = color.rgba(0, 0, 0, int(150 + (50 - sanity) * 2))
    if sanity < 30:
        # Hallucination effect - screen flashes
        if random.random() < 0.01:
            screen_flash.color = color.rgba(255, 0, 0, 50)
            invoke(setattr, screen_flash, 'color', color.rgba(255, 0, 0, 0), delay=0.1)
    if sanity <= 0:
        trigger_death()
    
    # Warning when ghost is close
    ghost_dist = distance(ghost.position, player.position)
    if ghost_dist < 10:
        warning_text.text = '! ! !'
        warning_text.color = color.rgba(255, 0, 0, int(255 * (1 - ghost_dist/10)))
        # Increase breathing intensity when ghost is near
        breathing_audio.volume = min(1.0, 0.4 + (10 - ghost_dist) * 0.06)
    else:
        warning_text.text = ''
        # Normal breathing volume
        breathing_audio.volume = 0.4
    
    # Heartbeat visual effect
    if heartbeat_intensity > 0.3:
        pulse = math.sin(time.time() * 8) * heartbeat_intensity * 0.02
        vignette.scale = Vec2(2 + pulse, 1 + pulse)
    
    # Check for exit
    if distance(player.position, exit_door.position) < 3:
        trigger_win()
    
    # Ambient sanity drain (psychological pressure)
    sanity = max(0, sanity - 0.1 * time.dt * (1 + ambient_fear))
    
    # Random creepy events
    if random.random() < 0.001:
        # Random light flicker burst
        for light in lights:
            light.is_on = False
            light.off_duration = random.uniform(0.5, 2)
    
    # Keep player in bounds
    player.position.x = max(-29, min(29, player.position.x))
    player.position.z = max(-29, min(29, player.position.z))

# ============================================================================
# START GAME
# ============================================================================
print("=" * 50)
print("SCREAM - Psychological Horror Game")
print("=" * 50)
print("OBJECTIVE: Find the EXIT and escape the house!")
print("WARNING: Avoid the ghost at all costs!")
print("CONTROLS: WASD to move, SHIFT to sprint, R to restart")
print("=" * 50)

app.run()
