from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math, random, time

fovY = 120
GRID_LENGTH = 600
rand_var = 423
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W / WIN_H

camera_pos = (0, 500, 500)
orbit_deg = 45.0
cam_height = 300.0
cam_radius = 1100.0
first_person = False

quadric = None
player_pos = [0.0, 0.0, 0.0]
player_angle = 0.0
player_speed = 260.0
player_turn_speed = 140.0
player_radius = 28.0

life = 5
score = 0
misses = 0
game_over = False
lie_down_amount = 0.0

NUM_ENEMIES = 5
enemies = []
bullets = []
BULLET_SPEED = 700.0
BULLET_SIZE = 10.0
BULLET_COOLDOWN = 0.18
last_shot_time = 0.0
max_bullet_age = 4.0

cheat_mode = False
cheat_auto_follow = False
auto_fire_fov_deg = 8.0
auto_fire_cooldown = 0.12

last_time = None
keys_down = set()

def clamp(v, lo, hi): return max(lo, min(hi, v))
def deg_to_rad(d): return d * math.pi / 180.0

def rand_spawn_pos():
    r = GRID_LENGTH * 0.85
    a = random.uniform(0, 2*math.pi)
    return r*math.cos(a), r*math.sin(a)

def reset_game():
    global life, score, misses, game_over, lie_down_amount, enemies, bullets
    global player_pos, player_angle, orbit_deg, cam_height, first_person
    life, score, misses = 5, 0, 0
    game_over = False
    lie_down_amount = 0.0
    bullets.clear()
    enemies.clear()
    for _ in range(NUM_ENEMIES):
        ex, ey = rand_spawn_pos()
        enemies.append({
            "x": ex, "y": ey,
            "base_r": random.uniform(16.0, 24.0),
            "pulse_t": random.uniform(0.0, 10.0),
            "speed": random.uniform(20.0, 40.0)
        })
    player_pos[:] = [0.0, 0.0, 0.0]
    player_angle = 0.0
    orbit_deg = 45.0
    cam_height = 300.0
    first_person = False

def draw_text(x, y, text):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(x, WIN_H - y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_checker_floor():
    step = 60
    half = GRID_LENGTH - 8  
    for x in range(-half, half, step):
        for y in range(-half, half, step):
            cx = (x + half)//step
            cy = (y + half)//step
            if (int(cx) + int(cy)) % 2 == 0:
                glColor3f(0.92, 0.90, 1.00)
            else:
                glColor3f(0.72, 0.57, 0.95)
            glBegin(GL_QUADS)
            glVertex3f(x, y, 0)
            glVertex3f(x+step, y, 0)
            glVertex3f(x+step, y+step, 0)
            glVertex3f(x, y+step, 0)
            glEnd()

def draw_walls():
    h = 120
    t = 8
    glColor3f(0.0, 0.2, 1.0)
    glPushMatrix(); glTranslatef(-GRID_LENGTH, 0, h/2); glScalef(t, GRID_LENGTH*2, h); glutSolidCube(1); glPopMatrix()
    glColor3f(0.0, 1.0, 0.2)
    glPushMatrix(); glTranslatef(GRID_LENGTH, 0, h/2); glScalef(t, GRID_LENGTH*2, h); glutSolidCube(1); glPopMatrix()
    glColor3f(0.2, 1.0, 1.0)
    glPushMatrix(); glTranslatef(0, GRID_LENGTH, h/2); glScalef(GRID_LENGTH*2, t, h); glutSolidCube(1); glPopMatrix()
    glColor3f(0.0, 0.4, 0.6)
    glPushMatrix(); glTranslatef(0,-GRID_LENGTH, h/2); glScalef(GRID_LENGTH*2, t, h); glutSolidCube(1); glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(lie_down_amount, 1, 0, 0)
    glRotatef(player_angle, 0, 0, 1)

    glColor3f(0.25, 0.55, 0.25)
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(26, 16, 64)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, 80)
    gluSphere(quadric, 16, 16, 16)
    glPopMatrix()

    glColor3f(0.5, 0.5, 0.5)
    for s in (-20, 20):
        glPushMatrix()
        glTranslatef(0, 0, 55)
        glRotatef(90, 0, 1, 0)
        glTranslatef(0, s, 0)
        gluCylinder(quadric, 4.5, 4.5, 20, 12, 1)
        glPopMatrix()

    glColor3f(1.0, 1.0, 1.0)
    for s in (-20, 20):
        glPushMatrix()
        glTranslatef(20, s, 55)
        glScalef(8, 8, 8)
        glutSolidCube(1)
        glPopMatrix()

    glColor3f(0.85, 0.85, 0.85)
    glPushMatrix()
    glTranslatef(-10, 0, 48)
    glScalef(16, 10, 24)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.1, 0.2, 1.0)
    for s in (-8, 8):
        glPushMatrix()
        glTranslatef(0, s, 10)
        glRotatef(90, 1, 0, 0)
        gluCylinder(quadric, 6.0, 6.0, 22.0, 12, 1)
        glPopMatrix()

    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(20, 0, 55)
    glScalef(20, 10, 8)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(35, 0, 55)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quadric, 3.5, 3.5, 30, 16, 1)
    glPopMatrix()

    glPopMatrix()

def gun_muzzle_world():
    mx, my, mz = 65.0, 0.0, 55.0
    a = deg_to_rad(player_angle)
    wx = player_pos[0] + mx*math.cos(a) - my*math.sin(a)
    wy = player_pos[1] + mx*math.sin(a) + my*math.cos(a)
    wz = player_pos[2] + mz
    return wx, wy, wz

def draw_enemy(e):
    t = e["pulse_t"]
    base = e["base_r"]
    r = base * (math.sin(t*2.2)*0.25 + 0.75)
    
    glPushMatrix()
    glTranslatef(e["x"], e["y"], r)
    
    glColor3f(0.95, 0.0, 0.0)
    gluSphere(quadric, r, 18, 18)
    
    glTranslatef(0, 0, r)
    glColor3f(0.0, 0.0, 0.0)
    gluSphere(quadric, r*0.5, 16, 16)
    
    glPopMatrix()

def draw_bullet(b):
    glPushMatrix()
    glTranslatef(b["x"], b["y"], b["z"])
    glScalef(BULLET_SIZE, BULLET_SIZE, BULLET_SIZE)
    glColor3f(1.0, 0.0, 0.0)
    glutSolidCube(1)
    glPopMatrix()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 2000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        mx, my, mz = gun_muzzle_world()
        a = deg_to_rad(player_angle)
        back, up = 18.0, 6.0
        cx = mx - math.cos(a)*back
        cy = my - math.sin(a)*back
        cz = mz + up
        tx = mx + math.cos(a)*50.0
        ty = my + math.sin(a)*50.0
        tz = mz

        if cheat_mode and cheat_auto_follow:
            tx = mx + math.cos(a)*80.0
            ty = my + math.sin(a)*80.0
            tz = mz

        gluLookAt(cx, cy, cz, tx, ty, tz, 0, 0, 1)
    else:
        cx = math.cos(deg_to_rad(orbit_deg)) * cam_radius
        cy = math.sin(deg_to_rad(orbit_deg)) * cam_radius
        cz = cam_height
        gluLookAt(cx, cy, cz, 0, 0, 0, 0, 0, 1)

def fire_bullet(now, cooldown=BULLET_COOLDOWN):
    global last_shot_time
    if now - last_shot_time < cooldown or game_over:
        return
    last_shot_time = now
    mx, my, mz = gun_muzzle_world()
    a = deg_to_rad(player_angle)
    dx, dy = math.cos(a), math.sin(a)
    bullets.append({
        "x": mx, "y": my, "z": mz,
        "dx": dx, "dy": dy,
        "speed": BULLET_SPEED,
        "size": BULLET_SIZE,
        "age": 0.0
    })

def line_of_fire_to_enemy(e):
    vx = e["x"] - player_pos[0]
    vy = e["y"] - player_pos[1]
    if vx == 0 and vy == 0: return False, 0.0
    target = math.degrees(math.atan2(vy, vx))
    diff = ((target - player_angle + 180) % 360) - 180
    return abs(diff) <= auto_fire_fov_deg, diff

def update_sim(dt, now):
    global life, score, misses, game_over, lie_down_amount, player_angle

    if game_over:
        lie_down_amount = clamp(lie_down_amount + 60.0*dt, 0.0, 90.0)
        return

    if cheat_mode:
        player_angle = (player_angle + player_turn_speed*dt) % 360
        for e in enemies:
            ok, _ = line_of_fire_to_enemy(e)
            if ok and (now - last_shot_time >= auto_fire_cooldown):
                fire_bullet(now)
                break

    for e in enemies:
        vx = player_pos[0] - e["x"]
        vy = player_pos[1] - e["y"]
        d = math.hypot(vx, vy)
        if d > 1e-3:
            ux, uy = vx/d, vy/d
            e["x"] += ux * e["speed"] * dt
            e["y"] += uy * e["speed"] * dt
        e["pulse_t"] += dt

    remove_idx = []
    for i, b in enumerate(bullets):
        b["x"] += b["dx"] * b["speed"] * dt
        b["y"] += b["dy"] * b["speed"] * dt
        b["age"] += dt

        if (abs(b["x"]) > GRID_LENGTH+40 or abs(b["y"]) > GRID_LENGTH+40 or b["age"] > max_bullet_age):
            remove_idx.append(i)
            misses += 1
            continue

        for j, e in enumerate(enemies):
            r = e["base_r"] * (math.sin(e["pulse_t"]*2.2)*0.25 + 0.75)
            dx, dy = b["x"]-e["x"], b["y"]-e["y"]
            if dx*dx + dy*dy <= (r + b["size"]*0.7)**2:
                remove_idx.append(i)
                score += 1
                ex, ey = rand_spawn_pos()
                enemies[j] = {
                    "x": ex, "y": ey,
                    "base_r": random.uniform(16.0, 24.0),
                    "pulse_t": 0.0,
                    "speed": random.uniform(20.0, 40.0)
                }
                break

    for idx in sorted(remove_idx, reverse=True):
        bullets.pop(idx)

    for e in enemies:
        r = e["base_r"] * (math.sin(e["pulse_t"]*2.2)*0.25 + 0.75)
        d = math.hypot(e["x"]-player_pos[0], e["y"]-player_pos[1])
        if d <= (r + player_radius*0.8):
            life -= 1
            ex, ey = rand_spawn_pos()
            e["x"], e["y"] = ex, ey

    if life <= 0 or misses >= 10:
        game_over = True

def keyboardListener(key, x, y):
    global cheat_mode, cheat_auto_follow, first_person
    key = key.lower()
    keys_down.add(key)
    
    if key == b'c':
        cheat_mode = not cheat_mode
        print(f"Cheat mode {'ON' if cheat_mode else 'OFF'}")
        
    elif key == b'v':
        if cheat_mode:  # Only allow auto-follow in cheat mode
            cheat_auto_follow = not cheat_auto_follow
            if cheat_auto_follow:
                first_person = True
            print(f"Auto-follow {'ON' if cheat_auto_follow else 'OFF'}")
            
    elif key == b'r':
        reset_game()
        print("Game reset")

def keyboardUpListener(key, x, y):
    key = key.lower()
    if key in keys_down: keys_down.remove(key)

def specialKeyListener(key, x, y):
    global orbit_deg, cam_height
    if key == GLUT_KEY_UP: cam_height = clamp(cam_height + 20.0, 120.0, 1000.0)
    if key == GLUT_KEY_DOWN: cam_height = clamp(cam_height - 20.0, 120.0, 1000.0)
    if key == GLUT_KEY_LEFT: orbit_deg -= 2.0
    if key == GLUT_KEY_RIGHT: orbit_deg += 2.0

def mouseListener(button, state, x, y):
    global first_person
    now = time.time()
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet(now)
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person

def handle_continuous_input(dt):
    global player_pos, player_angle
    if game_over: return
    
    forward = 0.0
    if b'w' in keys_down: forward += 1.0
    if b's' in keys_down: forward -= 1.0
    
    if forward != 0.0:
        a = deg_to_rad(player_angle)
        vx, vy = math.cos(a), math.sin(a)
        player_pos[0] += vx * player_speed * forward * dt
        player_pos[1] += vy * player_speed * forward * dt
        m = player_radius + 6.0
        player_pos[0] = clamp(player_pos[0], -GRID_LENGTH+m, GRID_LENGTH-m)
        player_pos[1] = clamp(player_pos[1], -GRID_LENGTH+m, GRID_LENGTH-m)
    
    if b'a' in keys_down: player_angle = (player_angle + 140.0*dt) % 360.0
    if b'd' in keys_down: player_angle = (player_angle - 140.0*dt) % 360.0

def idle():
    global last_time
    now = time.time()
    if last_time is None:
        last_time = now
    dt = now - last_time
    last_time = now

    handle_continuous_input(dt)
    update_sim(dt, now)
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WIN_W, WIN_H)
    
    setupCamera()
    draw_checker_floor()
    draw_walls()
    for e in enemies:
        draw_enemy(e)
    draw_player()
    for b in bullets:
        draw_bullet(b)
   
    
    draw_text(20, 30, f"Player Life Remaining: {life}")
    draw_text(20, 60, f"Game Score: {score}")
    draw_text(20, 90, f"Player Bullet Missed: {misses}")
    
    glutSwapBuffers()

def initGL():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

def main():
    global quadric
    random.seed(42)
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(10, 10)
    glutCreateWindow(b"3D Lab Assignment Template - Gun Game")

    quadric = gluNewQuadric()
    initGL()
    reset_game()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()