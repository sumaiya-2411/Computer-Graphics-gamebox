

import random 
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

wanted_level = 1
police_respawn_count = 0
MAX_WANTED_LEVEL = 10
police_visible = True
camera_pos = [0, 100, -300]   
fovY = 70
road_width = 600
track_segments = []  
t_param = 0
car_z = 0  
car_x = 0  
player_speed = 0.0 
player_angle = 0.0
car_x_vel = 0.0  
smoothed_center_x = 0.0
frame_count = 0  
player_path_history = []  
 
police_x = 0
police_z = -50
police_angle = 0.0
camera_mode = "third_person"
crashed = False
crash_timer = 0
CRASH_DURATION = 40  
police_spawned = False
police_message_timer = 0
POLICE_MESSAGE_DURATION = 80  
centerline_history = []
police_respawn_timer = 0
POLICE_RESPAWN_DELAY = 120  


police_disabled = False
collision_message_timer = 0
COLLISION_MESSAGE_DURATION = 80  
police_frozen = False


neon_glow_alpha = 0.5
neon_pulse_direction = 1
last_time = time.time()
slow_motion_active = False
slow_motion_timer = 0
SLOW_MO_DURATION = 300  
camera_shake_intensity = 0
camera_shake_timer = 0
police_light_toggle = False
last_light_toggle_time = time.time()
slow_mo_factor = 1.0  


# Input state
throttle_on = False
brake_on = False
steer_left = False
steer_right = False
neon_colors = [
    (0.0, 0.7, 1.0),  # Cyan
    (1.0, 0.0, 0.7),  # Magenta
    (0.0, 1.0, 0.3),  # Green
    (1.0, 0.5, 0.0),  # Orange
    (0.7, 0.0, 1.0),  # Purple
]
current_neon_color = 0
neon_color_timer = 0
NEON_COLOR_CHANGE_INTERVAL = 300  # frames
neon_intensity_base = 0.4
neon_intensity_pulse = 0.0
neon_pulse_speed = 0.05
multiple_glow_layers = True


def draw_text(x, y, text, size=GLUT_BITMAP_HELVETICA_18):
    """
    Renders 2D text at screen position (x, y).
    """
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1, 0, 0)  # Red text
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(size, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def get_centerline_x(z):
    """
    Interpolate centerline x from stored centerline_history.
    """
    if len(centerline_history) < 2:
        return 0.0

    for i in range(len(centerline_history) - 1):
        z0, cx0 = centerline_history[i]
        z1, cx1 = centerline_history[i + 1]

        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return cx0 + t * (cx1 - cx0)

    # If ahead of range
    return centerline_history[-1][1]


# ===============================
# Track Generation
# ===============================
def generate_track():
    global t_param, track_segments, centerline_history

    # Apply slow-mo factor to track generation
    track_speed_factor = 0.04 * slow_mo_factor
    x = 200 * math.sin(track_speed_factor * t_param)
    y = 0
    z = t_param * 40

    dx = 300 * 0.001 * math.cos(0.05 * t_param)
    dz = 40
    length = math.sqrt(dx * dx + dz * dz)
    if length == 0:
        length = 1

    nx = -dz / length
    nz = dx / length

    left = (x + nx * (road_width / 2), y, z + nz * (road_width / 2))
    right = (x - nx * (road_width / 2), y, z - nz * (road_width / 2))

    track_segments.append((left, right))

    # Calculate center_x and append to history
    center_x = (left[0] + right[0]) / 2
    centerline_history.append((z, center_x))

    t_param += 1


def draw_enhanced_neon_glow():
    """
    Enhanced neon glow 
    - Speed-responsive pulsation
    - Color cycling based on wanted level
    - Multiple glow layers for depth
    - Intensity boosted by police proximity
    """
    global neon_intensity_pulse, current_neon_color, neon_color_timer

    if len(track_segments) < 2:
        return

    # === Color Management ===
    neon_color_timer += 1
    if neon_color_timer >= NEON_COLOR_CHANGE_INTERVAL:
        neon_color_timer = 0
        current_neon_color = (current_neon_color + 1) % len(neon_colors)
    
    base_color = neon_colors[current_neon_color]
    if wanted_level >= 5:
        base_color = (min(base_color[0]+0.3,1.0), base_color[1]*0.7, base_color[2]*0.7)
    elif wanted_level >= 3:
        base_color = (min(base_color[0]+0.2,1.0), min(base_color[1]+0.1,1.0), base_color[2]*0.8)

    # === Intensity Calculation ===
    speed_factor = min(player_speed / 90.0, 1.0)
    base_intensity = 0.5 + speed_factor * 0.3
    
    neon_intensity_pulse += neon_pulse_speed * (1.0 + speed_factor)
    pulse_multiplier = 1.0 + 0.3 * math.sin(neon_intensity_pulse)
    
    proximity_boost = 1.0
    if police_spawned and not police_disabled:
        dx = car_x - police_x
        dz = car_z - police_z
        dist = math.sqrt(dx*dx + dz*dz)
        if dist < 200:
            proximity_boost = 1.0 + (200 - dist)/200 * 0.5
    
    final_intensity = min(base_intensity * pulse_multiplier * proximity_boost, 1.0)
    
    # === Glow Layers ===
    glow_layers = [
        {"width": 15, "intensity_mult": 1.0, "y_offset": -0.3},
        {"width": 25, "intensity_mult": 0.7, "y_offset": -0.5},
        {"width": 35, "intensity_mult": 0.4, "y_offset": -0.7},
    ]
    
    if multiple_glow_layers:
        for layer in glow_layers:
            width = layer["width"]
            y_off = layer["y_offset"]
            intensity = final_intensity * layer["intensity_mult"]
            
            glBegin(GL_QUADS)
            for i in range(len(track_segments)-1):
                left1, right1 = track_segments[i]
                left2, right2 = track_segments[i+1]
                
                r = min(base_color[0] * intensity, 1.0)
                g = min(base_color[1] * intensity, 1.0)
                b = min(base_color[2] * intensity, 1.0)
                glColor3f(r, g, b)
                
                # Left side glow quad
                glVertex3f(left1[0]-width, left1[1]+y_off, left1[2])
                glVertex3f(left2[0]-width, left2[1]+y_off, left2[2])
                glVertex3f(left2[0]+width, left2[1]+y_off, left2[2])
                glVertex3f(left1[0]+width, left1[1]+y_off, left1[2])
                
                # Right side glow quad
                glVertex3f(right1[0]-width, right1[1]+y_off, right1[2])
                glVertex3f(right2[0]-width, right2[1]+y_off, right2[2])
                glVertex3f(right2[0]+width, right2[1]+y_off, right2[2])
                glVertex3f(right1[0]+width, right1[1]+y_off, right1[2])
            glEnd()


def draw_speed_responsive_centerline():
  
    if len(track_segments) < 2:
        return

    # Speed-based width (4–12 units)
    speed_factor = min(player_speed / 90.0, 1.0)
    line_width = 4 + int(speed_factor * 8)
    
    # Color based on wanted level and speed
    if wanted_level >= 5:
        base_color = (1.0, 0.2, 0.2)  # Red
    elif wanted_level >= 3:
        base_color = (1.0, 0.6, 0.0)  # Orange
    else:
        base_color = (0.0, 1.0, 1.0)  # Cyan

    # Pulsation effect
    pulse_intensity = 0.7 + 0.3 * math.sin(frame_count * 0.1 * (1 + speed_factor))
    final_color = (
        base_color[0] * pulse_intensity,
        base_color[1] * pulse_intensity,
        base_color[2] * pulse_intensity
    )

    glColor3f(*final_color)

    # Draw centerline as a series of quads
    segment_length = 8
    gap_length = 4
    
    for i in range(0, len(track_segments) - 1, segment_length + gap_length):
        end_idx = min(i + segment_length, len(track_segments) - 1)
        for j in range(i, end_idx):
            left, right = track_segments[j]
            next_left, next_right = track_segments[j + 1]
            
            # Center points of current and next segment
            cx = (left[0] + right[0]) / 2
            cy = (left[1] + right[1]) / 2 + 0.15
            cz = (left[2] + right[2]) / 2
            
            next_cx = (next_left[0] + next_right[0]) / 2
            next_cy = (next_left[1] + next_right[1]) / 2 + 0.15
            next_cz = (next_left[2] + next_right[2]) / 2
            
            # Compute a perpendicular offset to simulate line width
            dx = next_cz - cz
            dz = -(next_cx - cx)
            length = math.sqrt(dx*dx + dz*dz)
            if length == 0:
                offset_x, offset_z = 0, 0
            else:
                offset_x = (dx / length) * line_width * 0.5
                offset_z = (dz / length) * line_width * 0.5
            
            # Draw quad for this segment
            glBegin(GL_QUADS)
            glVertex3f(cx - offset_x, cy, cz - offset_z)
            glVertex3f(cx + offset_x, cy, cz + offset_z)
            glVertex3f(next_cx + offset_x, next_cy, next_cz + offset_z)
            glVertex3f(next_cx - offset_x, next_cy, next_cz - offset_z)
            glEnd()


def draw_track():
    """
    Draws the road surface and center line.
    """
    if len(track_segments) < 2:
        return

    glColor3f(0.25, 0.0, 0.3)
    glBegin(GL_QUAD_STRIP)
    for (left, right) in track_segments:
        glVertex3f(*left)
        glVertex3f(*right)
    glEnd()

    # Draw center line
    glColor3f(0.0, 1.0, 1.0)
    glLineWidth(8)
    glBegin(GL_LINE_STRIP)
    for (left, right) in track_segments:
        cx = (left[0] + right[0]) / 2
        cy = (left[1] + right[1]) / 2 + 0.1
        cz = (left[2] + right[2]) / 2
        glVertex3f(cx, cy, cz)
    glEnd()


# ===============================
# Car
# ===============================







def draw_car():
    """
    Finalized car model:
    - Car body and roof are same color
    - Rear lights added on the back side
    - Wheels centered correctly
    """
    glPushMatrix()
    glTranslatef(car_x, 20, car_z)
    glRotatef(player_angle, 0, 1, 0)

    # ---- Car body dimensions ----
    body_length = 55.0
    body_height = 18.0
    body_width = 55.0
    body_y = 15.0

    # Common color for body and roof
    if crashed:
      body_color = (1.0, 0.0, 0.0)  # red when crashed
    else:
         body_color = (0.0, 0.1, 0.1)


    # ---- Draw car body ----
    glPushMatrix()
    glTranslatef(0, body_y, 0)
    glScalef(body_length, body_height, body_width)
    glColor3f(*body_color)
    glutSolidCube(1.2)
    glPopMatrix()

    # ---- Draw car roof (same color as body) ----
    glPushMatrix()
    glTranslatef(0, body_y + body_height / 2 + 12.0, 0)
    glScalef(body_length * 0.6, 10.0, body_width * 0.6)
    glColor3f(*body_color)
    glutSolidCube(1.2)
    glPopMatrix()

    # ---- Wheel parameters ----
    wheel_radius = 10.0
    wheel_width = 10
    wheel_y = 0.0
    wheel_offset_x = body_length / 2 - 4.0
    wheel_offset_z = body_width / 2 + 4.5
    wheel_color = (0.3, 0.3, 0.3)

    # ---- Draw 4 wheels ----
    for dx in [-wheel_offset_x, wheel_offset_x]:
        for dz in [-wheel_offset_z, wheel_offset_z]:
            glPushMatrix()
            glTranslatef(dx - wheel_width / 2.0, wheel_y, dz)
            glRotatef(90, 0, 1, 0)
            glColor3f(*wheel_color)
            gluCylinder(gluNewQuadric(), wheel_radius, wheel_radius, wheel_width, 16, 1)
            glPopMatrix()

    # ---- Draw back lights ----
        # ---- Draw back lights ----
     # ---- Draw back lights ----
    back_light_color = (1.0, 1.0, 0.3)  

    # Make sure lights appear just behind the scaled body
    back_z = -(body_width * 0.6)        # safely behind the body cube
    back_y = body_y + 9.5               # slightly above wheels, below roof
    light_offset_x = body_length / 2 - 8.0

    for x_offset in [-light_offset_x, light_offset_x]:
        glPushMatrix()
        glTranslatef(x_offset, back_y, back_z)
        glScalef(10.0, 5.0, 2.0)         # wider and flatter
        glColor3f(*back_light_color)
        glutSolidCube(1.0)
        glPopMatrix()



    glPopMatrix()


def draw_police_car():
    """
    Police car with:
    - Blue body
    - White roof
    - Red and blue flashing lightbar covering full roof (all sides)
    - Light grey wheels
    - Red back lights
    """
    glPushMatrix()
    glTranslatef(police_x, 20, police_z)
    glRotatef(police_angle, 0, 1, 0)



    # === Car Dimensions ===
    body_length = 55.0
    body_height = 18.0
    body_width = 55.0
    body_y = 15.0

    # === Colors ===
    body_color = (1.0, 1.0, 1.0)       
    roof_color = (1.0, 1.0, 1.0)       # White
    wheel_color = (0.3, 0.3, 0.3)      #  Grey
    back_light_color = (1.0, 0.0, 0.0) # Red

    # === Flashing Light Colors (alternate every 30 frames) ===
    flash_on = (frame_count // 30) % 2 == 0
    red_color = (0.5, 0.0, 0.0) if flash_on else (0.1, 0.0, 0.0)
    blue_color = (0.0, 0.0, 0.5) if flash_on else (0.0, 0.0, 0.1)

    # === Car Body ===
    glPushMatrix()
    glTranslatef(0, body_y, 0)
    glScalef(body_length, body_height, body_width)
    glColor3f(*body_color)
    glutSolidCube(1.2)
    glPopMatrix()

    # === Car Roof ===
    roof_length = body_length * 0.6
    roof_height = 10.0
    roof_width = body_width * 0.6
    roof_y = body_y + body_height / 2 + 12.0

    glPushMatrix()
    glTranslatef(0, roof_y, 0)
    glScalef(roof_length, roof_height, roof_width)
    glColor3f(*roof_color)
    glutSolidCube(1.2)
    glPopMatrix()

    # === Roof Lightbar Wrapping Full Roof (6 sides) ===
    half_l = roof_length * 0.6
    half_w = roof_width * 0.6
    roof_h = 6.0
    lightbar_y = roof_y + roof_height / 2 + 2.0

    glPushMatrix()
    glBegin(GL_QUADS)

    # --- TOP ---
    # Left (Red)
    glColor3f(*red_color)
    glVertex3f(-half_l, lightbar_y + roof_h, -half_w)
    glVertex3f(0.0,     lightbar_y + roof_h, -half_w)
    glVertex3f(0.0,     lightbar_y + roof_h,  half_w)
    glVertex3f(-half_l, lightbar_y + roof_h,  half_w)

    # Right (Blue)
    glColor3f(*blue_color)
    glVertex3f(0.0,      lightbar_y + roof_h, -half_w)
    glVertex3f(half_l,   lightbar_y + roof_h, -half_w)
    glVertex3f(half_l,   lightbar_y + roof_h,  half_w)
    glVertex3f(0.0,      lightbar_y + roof_h,  half_w)

    # --- FRONT ---
    glColor3f(*red_color)
    glVertex3f(-half_l, lightbar_y,       half_w)
    glVertex3f(0.0,     lightbar_y,       half_w)
    glVertex3f(0.0,     lightbar_y + roof_h, half_w)
    glVertex3f(-half_l, lightbar_y + roof_h, half_w)

    glColor3f(*blue_color)
    glVertex3f(0.0,      lightbar_y,       half_w)
    glVertex3f(half_l,   lightbar_y,       half_w)
    glVertex3f(half_l,   lightbar_y + roof_h, half_w)
    glVertex3f(0.0,      lightbar_y + roof_h, half_w)

    # --- BACK ---
    glColor3f(*red_color)
    glVertex3f(-half_l, lightbar_y,      -half_w)
    glVertex3f(0.0,     lightbar_y,      -half_w)
    glVertex3f(0.0,     lightbar_y + roof_h, -half_w)
    glVertex3f(-half_l, lightbar_y + roof_h, -half_w)

    glColor3f(*blue_color)
    glVertex3f(0.0,      lightbar_y,      -half_w)
    glVertex3f(half_l,   lightbar_y,      -half_w)
    glVertex3f(half_l,   lightbar_y + roof_h, -half_w)
    glVertex3f(0.0,      lightbar_y + roof_h, -half_w)

    # --- LEFT SIDE (Red) ---
    glColor3f(*red_color)
    glVertex3f(-half_l, lightbar_y,      -half_w)
    glVertex3f(-half_l, lightbar_y,       half_w)
    glVertex3f(-half_l, lightbar_y + roof_h, half_w)
    glVertex3f(-half_l, lightbar_y + roof_h, -half_w)

    # --- RIGHT SIDE (Blue) ---
    glColor3f(*blue_color)
    glVertex3f(half_l, lightbar_y,      -half_w)
    glVertex3f(half_l, lightbar_y,       half_w)
    glVertex3f(half_l, lightbar_y + roof_h, half_w)
    glVertex3f(half_l, lightbar_y + roof_h, -half_w)

    glEnd()
    glPopMatrix()



    # === Wheels ===
    wheel_radius = 10.0
    wheel_width = 10
    wheel_y = 0.0
    wheel_offset_x = body_length / 2 - 4.0
    wheel_offset_z = body_width / 2 + 4.5

    for dx in [-wheel_offset_x, wheel_offset_x]:
        for dz in [-wheel_offset_z, wheel_offset_z]:
            glPushMatrix()
            glTranslatef(dx - wheel_width / 2.0, wheel_y, dz)
            glRotatef(90, 0, 1, 0)
            glColor3f(*wheel_color)
            gluCylinder(gluNewQuadric(), wheel_radius, wheel_radius, wheel_width, 16, 1)
            glPopMatrix()

    # === Back Lights ===
    back_z = -(body_width * 0.6)
    back_y = body_y + 9.5
    light_offset_x = body_length / 2 - 8.0

    for x_offset in [-light_offset_x, light_offset_x]:
        glPushMatrix()
        glTranslatef(x_offset, back_y, back_z)
        glScalef(10.0, 5.0, 2.0)
        glColor3f(*back_light_color)
        glutSolidCube(1.0)
        glPopMatrix()

    glPopMatrix()

def draw_police_lights(): 
    """
    Draws rotating police lights on top of police car.
    """
    global police_light_toggle, last_light_toggle_time
    
    # Toggle lights every 250ms
    current_time = time.time()
    if current_time - last_light_toggle_time > 0.25:
        police_light_toggle = not police_light_toggle
        last_light_toggle_time = current_time
    
    glPushMatrix()
    glTranslatef(police_x, 20, police_z)
    glRotatef(police_angle, 0, 1, 0)
    
    # Lightbar dimensions
    lightbar_length = 25.0
    lightbar_width = 10.0
    lightbar_height = 5.0
    lightbar_y = 45.0  # Position on top of car
    
    # Draw lightbar base
    glPushMatrix()
    glTranslatef(0, lightbar_y, 0)
    glScalef(lightbar_length, lightbar_height, lightbar_width)
    glColor3f(0.2, 0.2, 0.2)  # Dark gray base
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Draw rotating lights
    glPushMatrix()
    glTranslatef(0, lightbar_y + lightbar_height/2 + 2.0, 0)
    
    # Rotate lights over time
    rotation_angle = (current_time * 360) % 360
    glRotatef(rotation_angle, 0, 1, 0)
    
    # Draw red and blue lights
    if police_light_toggle:
        # Red light
        glPushMatrix()
        glTranslatef(5, 0, 0)
        glColor3f(1.0, 0.0, 0.0)
        glutSolidSphere(2.5, 10, 10)
        glPopMatrix()
        
        # Blue light
        glPushMatrix()
        glTranslatef(-5, 0, 0)
        glColor3f(0.0, 0.0, 1.0)
        glutSolidSphere(2.5, 10, 10)
        glPopMatrix()
    else:
        # Alternate pattern
        glPushMatrix()
        glTranslatef(0, 0, 5)
        glColor3f(1.0, 0.0, 0.0)
        glutSolidSphere(2.5, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0, -5)
        glColor3f(0.0, 0.0, 1.0)
        glutSolidSphere(2.5, 10, 10)
        glPopMatrix()
    
    glPopMatrix()
    glPopMatrix()









def keyboardListener(key, x, y):    
    global throttle_on, brake_on, steer_left, steer_right, slow_motion_active, slow_motion_timer
    
    if key == b'w':
        throttle_on = True
    if key == b's':
        brake_on = True
    if key == b'a':
        steer_left = True
    if key == b'd':
        steer_right = True
    if key == b'r' and crashed:
        reset_game()
    if key == b't' or key == b'T':
        # Activate slow-mo power-up
        if not slow_motion_active:
            slow_motion_active = True
            slow_motion_timer = SLOW_MO_DURATION
            print("Slow-motion activated!")

def keyboardUpListener(key, x, y):    
    global throttle_on, brake_on, steer_left, steer_right
    global slow_motion_active, slow_motion_timer, police_frozen, police_visible
    
    if key == b'w':
        throttle_on = False
    if key == b's':
        brake_on = False
    if key == b'a':
        steer_left = False
    if key == b'd':
        steer_right = False
 

def specialKeyListener(key, x, y):
    """
    Map arrow keys to steering like a racing game.
    """
    global steer_left, steer_right
    if key == GLUT_KEY_LEFT:
        steer_left = True
    if key == GLUT_KEY_RIGHT:
        steer_right = True


def specialKeyUpListener(key, x, y):
    global steer_left, steer_right
    if key == GLUT_KEY_LEFT:
        steer_left = False
    if key == GLUT_KEY_RIGHT:
        steer_right = False


def mouseButton(button, state, x, y):
    global camera_mode

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if camera_mode == "third_person":
            camera_mode = "hood"
        else:
            camera_mode = "third_person"



def setupCamera():  
    global camera_shake_intensity, camera_shake_timer, fovY
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    # Dynamic FOV based on police proximity
    dynamic_fov = fovY
    if police_spawned and not police_disabled:
        # Calculate distance to police
        dx = car_x - police_x
        dz = car_z - police_z
        dist = math.sqrt(dx * dx + dz * dz)
        
        # Zoom out when police are close (within 200 units)
        if dist < 200:
            zoom_factor = 1.0 + (200 - dist) / 200 * 0.5  # Up to 1.5x zoom
            dynamic_fov = fovY * zoom_factor
    
    gluPerspective(dynamic_fov, 1.25, 1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Apply camera shake if active
    shake_x = 0
    shake_y = 0
    if camera_shake_timer > 0:
        shake_x = random.uniform(-camera_shake_intensity, camera_shake_intensity)
        shake_y = random.uniform(-camera_shake_intensity, camera_shake_intensity)
        camera_shake_timer -= 1

    if camera_mode == "third_person":
        # Third-person camera: follows car from behind and above
        cam_x = car_x + shake_x
        cam_y = 150 + shake_y
        cam_z = car_z - 300

        look_x = car_x
        look_y = 20
        look_z = car_z + 200

        gluLookAt(cam_x, cam_y, cam_z,
                  look_x, look_y, look_z,
                  0, 1, 0)

    elif camera_mode == "hood":
        # First-person/hood view: just above and behind front of car
        eye_x = car_x + shake_x
        eye_y = 50 + shake_y     # Slightly above car roof
        eye_z = car_z + 25       # Near front of car

        look_x = car_x
        look_y = 40
        look_z = car_z + 200

        gluLookAt(eye_x, eye_y, eye_z,
                  look_x, look_y, look_z,
                  0, 1, 0)


def trigger_camera_shake(intensity=5.0, duration=20):
    """
    Trigger camera shake effect.
    """
    global camera_shake_intensity, camera_shake_timer
    camera_shake_intensity = intensity
    camera_shake_timer = duration

def reset_game():
    global car_x, car_z, player_speed, player_angle, car_x_vel,wanted_level, police_respawn_count
    global police_x, police_z, police_angle, player_path_history,collision_message_timer,police_frozen
    global track_segments, t_param, crashed, crash_timer,police_spawned,police_message_timer,police_disabled,police_respawn_timer,POLICE_RESPAWN_DELAY
    global slow_motion_active, slow_motion_timer, slow_mo_factor, police_visible

    car_x = 0
    car_z = 0
    player_speed = 0.0
    player_angle = 0.0
    car_x_vel = 0.0
    player_path_history.clear()
    police_disabled = False
    collision_message_timer = 0

    police_x = 0
    police_z = -50
    police_angle = 0.0
    t_param = 0
    crashed = False
    police_spawned = False
    police_frozen = False
    police_visible = True  # Reset police visibility
    police_respawn_timer = 0

    police_message_timer = 0
    crash_timer = 0
    wanted_level = 1
    police_respawn_count = 0
    track_segments.clear()
    
    # Reset slow-mo
    slow_motion_active = False
    slow_motion_timer = 0
    slow_mo_factor = 1.0
    
    for _ in range(180):
        generate_track()


def idle():
    global car_z, car_x, player_speed, player_angle, frame_count, spawn_chance
    global player_path_history, police_x, police_z, police_angle
    global crashed, crash_timer, police_spawned, police_message_timer
    global collision_message_timer, police_disabled, police_frozen, police_respawn_timer
    global wanted_level, police_respawn_count, slow_motion_active, slow_motion_timer
    global police_visible

    # === Handle slow-motion timer and INSTANT police chase ===
    if slow_motion_active:
        slow_motion_timer -= 1
        if slow_motion_timer <= 0:
            slow_motion_active = False
            police_frozen = False     # Unfreeze police
            police_visible = True     # Make police visible
            
            # INSTANTLY teleport police close behind player for immediate chase
            if police_spawned and not police_disabled:
                police_z = car_z - 80   # Place police 80 units behind player
                police_x = car_x + random.uniform(-30, 30)  # Slightly offset left/right
                police_angle = 0.0
                print("Police teleported close - IMMEDIATE CHASE!")

    if crashed:
        glutPostRedisplay()
        return

    # === Handle police re-spawn logic (AFTER COLLISION) ===
    if police_disabled and not police_spawned and not crashed and player_speed > 50.0 and police_respawn_timer <= 0:
        police_disabled = False
        police_frozen = False
        police_spawned = True
        police_visible = True
        police_message_timer = POLICE_MESSAGE_DURATION

        spawn_distance = 200.0
        target_z = car_z - spawn_distance
        closest_x = get_centerline_x(target_z)

        for i in range(len(player_path_history) - 1):
            z0, x0 = player_path_history[i]
            z1, x1 = player_path_history[i + 1]
            if z0 <= target_z <= z1:
                t = (target_z - z0) / (z1 - z0)
                closest_x = x0 + t * (x1 - x0)
                break

        police_z = target_z
        police_x = closest_x
        police_angle = 0.0
        police_respawn_count += 1
        wanted_level = min(wanted_level + 1, MAX_WANTED_LEVEL)
        print(f"[DEBUG] Police spawn triggered due to speeding again. Wanted Level: {wanted_level}")

    # === Handle initial police spawn logic ===
    if not police_spawned and not police_disabled and player_speed > 50.0:
        spawn_chance = 0.02 * wanted_level
        if random.random() < spawn_chance:
            police_spawned = True
            police_visible = True
            police_message_timer = POLICE_MESSAGE_DURATION

            spawn_distance = 200.0
            target_z = car_z - spawn_distance
            closest_x = get_centerline_x(target_z)

            for i in range(len(player_path_history) - 1):
                z0, x0 = player_path_history[i]
                z1, x1 = player_path_history[i + 1]
                if z0 <= target_z <= z1:
                    t = (target_z - z0) / (z1 - z0)
                    closest_x = x0 + t * (x1 - x0)
                    break

            police_z = target_z
            police_x = closest_x
            police_angle = 0.0

            police_respawn_count += 1
            wanted_level = min(wanted_level + 1, MAX_WANTED_LEVEL)
            print(f"[DEBUG] Police spawn triggered. Wanted Level: {wanted_level}, Chance: {spawn_chance:.2f}")

    # === Police collision detection ===
    if police_spawned and not police_disabled and police_visible and not police_frozen:
        dx = car_x - police_x
        dz = car_z - police_z
        distance = math.sqrt(dx * dx + dz * dz)

        if distance < 55.0:
            print(f"[DEBUG] Police collision detected - Distance: {distance:.1f} - GAME OVER!")
            crashed = True
            crash_timer = CRASH_DURATION
            police_disabled = True
            police_spawned = False
            police_visible = False
            trigger_camera_shake(15.0, 50)

    frame_count += 1

    # === Player movement ===
    max_speed = 90.0
    accel = 0.1
    brake = 2.0
    max_steer = 24.0
    steer_ease = 0.2
    steer_speed = 3.0
    base_recenter_lerp = 0.08

    if throttle_on:
        player_speed = min(player_speed + accel, max_speed)
    elif brake_on:
        player_speed = max(player_speed - brake, 0.0)
    else:
        player_speed *= 0.99
        if player_speed < 0.05:
            player_speed = 0.0

    car_z += player_speed

    center_x = get_centerline_x(car_z)
    speed_factor = min(max(player_speed / max_speed, 0.0), 1.0)

    steer_input = 0.0
    if steer_left:
        steer_input -= 1.0
    if steer_right:
        steer_input += 1.0

    target_angle = steer_input * max_steer * (0.3 + 0.7 * speed_factor)
    player_angle += (target_angle - player_angle) * steer_ease
    player_angle = max(min(player_angle, max_steer), -max_steer)

    if abs(steer_input) > 0.0:
        car_x += steer_input * steer_speed
    else:
        offset = center_x - car_x
        car_x += offset * base_recenter_lerp

    margin = (road_width * 0.5) - 18.0
    if abs(car_x - center_x) > margin:
        if not crashed:
            crashed = True
            crash_timer = CRASH_DURATION
            print("[DEBUG] Crash - out of road bounds.")
            trigger_camera_shake(10.0, 40)
        car_x = max(min(car_x, center_x + margin), center_x - margin)

    player_path_history.append((car_z, car_x))
    if len(player_path_history) > 400:
        player_path_history.pop(0)

    # === Police chasing logic (IMMEDIATE and AGGRESSIVE chase) ===
    if police_spawned and not police_frozen and not police_disabled and police_visible:
        dx = car_x - police_x
        dz = car_z - police_z
        dist = math.sqrt(dx * dx + dz * dz)

        if dist > 1.0:
            # Police chase - just slightly faster than player (original balance)
            target_speed = max(player_speed * 1.01, 30.0)  # Just 1% faster like original
            max_chase_speed = 110.0  # Original max speed
            actual_speed = min(target_speed, max_chase_speed)
            move_step = min(actual_speed, dist)

            angle_rad = math.atan2(dx, dz)
            police_angle = math.degrees(angle_rad)

            police_x += math.sin(angle_rad) * move_step
            police_z += math.cos(angle_rad) * move_step

            # Keep police on road
            center_police_x = get_centerline_x(police_z)
            margin = (road_width * 0.5) - 18.0
            police_x = max(min(police_x, center_police_x + margin), center_police_x - margin)

    # === Track generation ahead ===
    if len(track_segments) > 0:
        last_z = track_segments[-1][0][2]
        if car_z + 1200 > last_z:
            for _ in range(12):
                generate_track()

    # === Timers ===
    if crashed:
        crash_timer -= 1
        if crash_timer <= 0:
            crashed = False
            police_disabled = False

    if police_message_timer > 0:
        police_message_timer -= 1

    if collision_message_timer > 0:
        collision_message_timer -= 1

    if police_respawn_timer > 0:
        police_respawn_timer -= 1

    glutPostRedisplay()

def enhanced_showScreen():
    """
    Enhanced rendering function with police visibility control.
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    
    # === Draw all visual effects in proper order ===
    draw_enhanced_neon_glow()      # Enhanced neon glow beneath track
    draw_track()                   # Original track
    draw_speed_responsive_centerline()  # Enhanced centerline
    draw_road_markings_glow()      # Glowing side markings
    
    draw_car()                     # Original car
    
    # === Enhanced crash effects ===
    if crashed:
        draw_crash_effects()
        draw_text(400, 700, "MISSION FAILED", GLUT_BITMAP_HELVETICA_18)
        draw_text(380, 650, "PRESS R TO RESTART", GLUT_BITMAP_HELVETICA_18)

    # === Police effects (only draw if visible) ===
    if police_message_timer > 0:
        draw_text(380, 650, "POLICE ALERT", GLUT_BITMAP_HELVETICA_18)
    
    if police_spawned and police_visible:
        draw_enhanced_police_effects()  # Enhanced police effects
        draw_police_car()               # Original police car
    
    if collision_message_timer > 0:
        draw_text(360, 600, "Collision with police, Fake escape", GLUT_BITMAP_HELVETICA_18)
    
    # === UI Elements ===
    speed_text = f"Speed: {player_speed:.1f} u/s"
    draw_text(20, 760, speed_text, GLUT_BITMAP_HELVETICA_18)
    wanted_text = f"Wanted Level: {wanted_level}"
    draw_text(20, 730, wanted_text, GLUT_BITMAP_HELVETICA_18)
    
    # === Enhanced speed warnings with color ===
    if player_speed > 80.0:
        # Flash warning text
        if int(frame_count / 10) % 2:  # Flash every 10 frames
            draw_text(20, 700, "WARNING: HIGH SPEED!", GLUT_BITMAP_HELVETICA_18)
    elif player_speed < 20.0 and throttle_on:
        draw_text(20, 700, "Too slow! Speed up!", GLUT_BITMAP_HELVETICA_18)
    
    # === Slow-mo UI ===
    if slow_motion_active:
        draw_text(20, 670, "SLOW-MO ACTIVE!", GLUT_BITMAP_HELVETICA_18)
        time_left = slow_motion_timer // 60
        draw_text(20, 640, f"Time left: {time_left}s", GLUT_BITMAP_HELVETICA_18)
        draw_text(20, 610, "Police Slowed down!", GLUT_BITMAP_HELVETICA_18)

    glutSwapBuffers()



def draw_road_markings_glow():
    """
    Glowing road markings (simulated with pulsing brightness).
    """
    if len(track_segments) < 4:
        return
    
    # Pulsating brightness instead of alpha
    pulse = 0.5 + 0.3 * math.sin(frame_count * 0.08)
    
    left_color = (0.0, pulse, 0.5)    # Green-cyan
    right_color = (pulse, 0.5, 0.0)   # Orange
    
    marking_width = 8
    marking_height = 0.2
    
    glBegin(GL_QUADS)
    for i in range(0, len(track_segments) - 1, 8):
        if i + 3 >= len(track_segments):
            break
        
        left1, right1 = track_segments[i]
        left2, right2 = track_segments[i + 3]
        
        # Left marking
        glColor3f(*left_color)
        glVertex3f(left1[0], left1[1] + marking_height, left1[2])
        glVertex3f(left2[0], left2[1] + marking_height, left2[2])
        glVertex3f(left2[0] + marking_width, left2[1] + marking_height, left2[2])
        glVertex3f(left1[0] + marking_width, left1[1] + marking_height, left1[2])
        
        # Right marking
        glColor3f(*right_color)
        glVertex3f(right1[0], right1[1] + marking_height, right1[2])
        glVertex3f(right2[0], right2[1] + marking_height, right2[2])
        glVertex3f(right2[0] - marking_width, right2[1] + marking_height, right2[2])
        glVertex3f(right1[0] - marking_width, right1[1] + marking_height, right1[2])
    glEnd()




def draw_crash_effects():
    """
    Visual effects when crashed (flashing overlay + sparks).
    """
    if not crashed:
        return
    
    # Flashing red overlay
    flash = 0.3 + 0.2 * math.sin(crash_timer * 0.5)
    glColor3f(flash, 0.0, 0.0)
    overlay_size = 500
    
    glBegin(GL_QUADS)
    glVertex3f(car_x - overlay_size, 200, car_z - overlay_size)
    glVertex3f(car_x + overlay_size, 200, car_z - overlay_size)
    glVertex3f(car_x + overlay_size, 200, car_z + overlay_size)
    glVertex3f(car_x - overlay_size, 200, car_z + overlay_size)
    glEnd()
    
    # Sparks (yellow points)
    for i in range(10):
        spark_x = car_x + random.uniform(-30, 30)
        spark_z = car_z + random.uniform(-30, 30)
        spark_y = 15 + random.uniform(0, 20)
        
        glPointSize(4.0)
        glBegin(GL_POINTS)
        glColor3f(1.0, 1.0, 0.0)
        glVertex3f(spark_x, spark_y, spark_z)
        glEnd()

def draw_enhanced_police_effects():
    """
    Enhanced police effects (flashing aura + beams).
    """
    if not police_spawned or police_disabled:
        return
    
    # Alternating siren colors (red/blue)
    current_time = time.time()
    siren_cycle = int(current_time * 4) % 2
    if siren_cycle == 0:
        siren_color = (0.3, 0.0, 0.0)
    else:
        siren_color = (0.0, 0.0, 0.3)
    
    aura_size = 60 + 20 * math.sin(current_time * 8)
    
    # Draw aura quad
    glBegin(GL_QUADS)
    glColor3f(*siren_color)
    glVertex3f(police_x - aura_size, 2, police_z - aura_size)
    glVertex3f(police_x + aura_size, 2, police_z - aura_size)
    glVertex3f(police_x + aura_size, 2, police_z + aura_size)
    glVertex3f(police_x - aura_size, 2, police_z + aura_size)
    glEnd()
    
    # Draw beam toward car (yellow, fading by distance)
    if not crashed:
        dx = car_x - police_x
        dz = car_z - police_z
        dist = math.sqrt(dx * dx + dz * dz)
        if dist < 300:
            fade = (300 - dist) / 300
            glColor3f(1.0 * fade, 1.0 * fade, 0.0)
            glBegin(GL_TRIANGLES)
            glVertex3f(police_x, 25, police_z)
            glVertex3f(car_x - 20, 5, car_z)
            glVertex3f(car_x + 20, 5, car_z)
            glEnd()




def enhanced_showScreen():
    """
    Enhanced rendering function with police visibility control.
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    
    # === Draw all visual effects in proper order ===
    draw_enhanced_neon_glow()      # Enhanced neon glow beneath track
    draw_track()                   # Original track
    draw_speed_responsive_centerline()  # Enhanced centerline
    draw_road_markings_glow()      # Glowing side markings
  
    draw_car()                     # Original car
    
    # === Enhanced crash effects ===
    if crashed:
        draw_crash_effects()
        draw_text(400, 700, "MISSION FAILED", GLUT_BITMAP_HELVETICA_18)
        draw_text(380, 650, "PRESS R TO RESTART", GLUT_BITMAP_HELVETICA_18)

    # === Police effects (only draw if visible) ===
    if police_message_timer > 0:
        draw_text(380, 650, "POLICE ALERT", GLUT_BITMAP_HELVETICA_18)
    
    if police_spawned and police_visible:
        draw_enhanced_police_effects()  # Enhanced police effects
        draw_police_car()               # Original police car
    
    if collision_message_timer > 0:
        draw_text(360, 600, "Collision with police, Fake escape", GLUT_BITMAP_HELVETICA_18)
    
    # === UI Elements ===
    speed_text = f"Speed: {player_speed:.1f} u/s"
    draw_text(20, 760, speed_text, GLUT_BITMAP_HELVETICA_18)
    wanted_text = f"Wanted Level: {wanted_level}"
    draw_text(20, 730, wanted_text, GLUT_BITMAP_HELVETICA_18)
    
    # === Enhanced speed warnings with color ===
    if player_speed > 80.0:
        # Flash warning text
        if int(frame_count / 10) % 2:  # Flash every 10 frames
            draw_text(20, 700, "WARNING: HIGH SPEED!", GLUT_BITMAP_HELVETICA_18)
    elif player_speed < 20.0 and throttle_on:
        draw_text(20, 700, "Too slow! Speed up!", GLUT_BITMAP_HELVETICA_18)
    
    # === Slow-mo UI ===
    if slow_motion_active:
        draw_text(20, 670, "SLOW-MO ACTIVE!", GLUT_BITMAP_HELVETICA_18)
        time_left = slow_motion_timer // 60
        draw_text(20, 640, f"Time left: {time_left}s", GLUT_BITMAP_HELVETICA_18)
        draw_text(20, 610, "Police frozen!", GLUT_BITMAP_HELVETICA_18)
   
    glutSwapBuffers()


# ===============================
# Main
# ===============================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Neon Racer - Enhanced Visuals")

    glEnable(GL_DEPTH_TEST)

  
    for _ in range(180):
        generate_track()

    glutDisplayFunc(enhanced_showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialKeyUpListener)
    glutMouseFunc(mouseButton)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()     












