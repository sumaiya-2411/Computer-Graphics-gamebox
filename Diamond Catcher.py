
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

window_width = 500
window_height = 700
diamond_size = 15
catcher_width = 100
catcher_height = 20
diamond_speed = 150  
caught_count = 0
game_running = True
game_paused = False
game_over = False
last_frame_time = 0.0
catcher_x = window_width // 2
catcher_y = 50

diamond = None  
catcher_color = (1, 1, 1)
diamond_new_cooldown = 0.0  


def random_color():
    
    return (random.uniform(0.5,1.0), random.uniform(0.5,1.0), random.uniform(0.5,1.0))


def draw_line_midpoint(p1, p2):  # Midpoint line algorithm diye line draw korar function
    x1, y1 = map(int, p1)
    x2, y2 = map(int, p2)

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1

    if dy <= dx:
        d = 2 * dy - dx
        y = y1
        for x in range(x1, x2 + sx, sx):
            glBegin(GL_POINTS)
            glVertex2i(x, y)
            glEnd()
            if d > 0:
                y += sy
                d -= 2 * dx
            d += 2 * dy
    else:
        d = 2 * dx - dy
        x = x1
        for y in range(y1, y2 + sy, sy):
            glBegin(GL_POINTS)
            glVertex2i(x, y)
            glEnd()
            if d > 0:
                x += sx
                d -= 2 * dy
            d += 2 * dx

def draw_diamond(x, y, size, color):
   
    glColor3f(*color)
    top = (x, y + size)
    right = (x + size, y)
    bottom = (x, y - size)
    left = (x - size, y)

    draw_line_midpoint(top, right)
    draw_line_midpoint(right, bottom)
    draw_line_midpoint(bottom, left)
    draw_line_midpoint(left, top)

def draw_catcher(cx, cy, width, height, color):
    
    glColor3f(*color)
    # top_left = (cx - width // 2 + 10, cy + height)
    # top_right = (cx + width // 2 - 10, cy + height)
    # bottom_left = (cx - width // 2, cy)
    # bottom_right = (cx + width // 2, cy)
    top_left = (cx - width // 2, cy + height)
    top_right = (cx + width // 2, cy + height)
    bottom_left = (cx - width // 2 + 10, cy)
    bottom_right = (cx + width // 2 - 10, cy)


    draw_line_midpoint(bottom_left, top_left)
    draw_line_midpoint(top_left, top_right)
    draw_line_midpoint(top_right, bottom_right)
    draw_line_midpoint(bottom_right, bottom_left)

def draw_ui_buttons():
   
    glColor3f(0, 1, 1)  
    draw_line_midpoint((20, 670), (40, 680))
    draw_line_midpoint((20, 670), (40, 660))
    
   
    glColor3f(1, 0.65, 0)  
    if game_paused:
       
        draw_line_midpoint((245, 660), (265, 670))
        draw_line_midpoint((245, 680), (265, 670))
        draw_line_midpoint((245, 660), (245, 680))
    else:
       
        draw_line_midpoint((245, 660), (245, 680))
        draw_line_midpoint((255, 660), (255, 680))

    
    glColor3f(1, 0, 0)
    draw_line_midpoint((470, 680), (490, 660))
    draw_line_midpoint((490, 680), (470, 660))

def draw_text(x, y, text, color=(1, 1, 1)):
    
    glColor3f(*color)
    glRasterPos2i(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def new_diamond():
    global diamond
    if diamond is None:
       
        x = random.randint(diamond_size, window_width - diamond_size)
        y = window_height
        color = random_color()
        diamond = {'x': x, 'y': y, 'color': color}

def check_collision(d):
   
    d_left = d['x'] - diamond_size
    d_right = d['x'] + diamond_size
    d_bottom = d['y'] - diamond_size
    d_top = d['y'] + diamond_size

    c_left = catcher_x - catcher_width // 2
    c_right = catcher_x + catcher_width // 2
    c_bottom = catcher_y
    c_top = catcher_y + catcher_height

    overlap_x = (d_left < c_right) and (d_right > c_left)
    overlap_y = (d_bottom < c_top) and (d_top > c_bottom)

    return overlap_x and overlap_y

def reset_game():
   
    global caught_count, game_running, game_paused, game_over, diamond_speed, diamond, catcher_x, catcher_color, diamond_new_cooldown
    caught_count = 0
    game_running = True
    game_paused = False
    game_over = False
    diamond_speed = 150
    catcher_x = window_width // 2
    catcher_color = (1,1,1)
    diamond = None
    diamond_new_cooldown = 0.0
    new_diamond()
    print("Starting Over") 

def display():
    glClear(GL_COLOR_BUFFER_BIT)

    if diamond:
        draw_diamond(diamond['x'], int(diamond['y']), diamond_size, diamond['color'])

    draw_catcher(catcher_x, catcher_y, catcher_width, catcher_height, catcher_color)
    draw_ui_buttons()

    if game_over:
        
        draw_text(window_width // 2 - 50, window_height // 2, "GAME OVER", color=(1, 0, 0))

    score_text = f"Score: {caught_count}"
    draw_text(10, window_height - 30, score_text, color=(1, 1, 1))

    glutSwapBuffers()

def keyboard_special_down(key, x, y):
    global catcher_x
    if not game_over and not game_paused:
       
        if key == GLUT_KEY_LEFT:
            catcher_x = max(catcher_x - 20, catcher_width // 2) 
        elif key == GLUT_KEY_RIGHT:
            catcher_x = min(catcher_x + 20, window_width - catcher_width // 2)

def mouse_click(button, state, x, y):
    global game_paused, game_running, game_over, catcher_color, caught_count, diamond_speed, diamond

    if state != GLUT_DOWN:
        return
    y = window_height - y 

    def point_in_box(px, py, box):
        
        bx, by, bw, bh = box
        return bx <= px <= bx + bw and by <= py <= by + bh

   
    restart_box = (20, 660, 20, 20)
    pause_box = (240, 660, 20, 20)
    quit_box = (470, 660, 20, 20)

    if point_in_box(x, y, restart_box):
        reset_game()
    elif point_in_box(x, y, pause_box):
        if not game_over:
            game_paused = not game_paused
            print("Paused" if game_paused else "Resumed")
    elif point_in_box(x, y, quit_box):
        print(f"Goodbye. Final Score: {caught_count}")
        glutLeaveMainLoop()  

def idle():
    global last_frame_time, diamond_new_cooldown, diamond, game_running, game_paused, game_over, diamond_speed, caught_count, catcher_color

    current_time = time.time()
    if last_frame_time == 0.0:
        last_frame_time = current_time
    delta = current_time - last_frame_time
    last_frame_time = current_time

    
    if game_running and not game_paused and not game_over:
        
        if diamond:
            diamond['y'] -= diamond_speed * delta  

            if check_collision(diamond):
                caught_count += 1
                print(f"Score: {caught_count}")
                diamond_speed += 10  
                diamond = None  
            elif diamond['y'] < 0:
                
                game_over = True
                game_running = False
                catcher_color = (1, 0, 0) 
                diamond = None
                print(f"Game Over. Final Score: {caught_count}")

        if diamond is None:
            diamond_new_cooldown += delta
            if diamond_new_cooldown >= 1.0:  # 1 second por notun diamond 
                new_diamond()
                diamond_new_cooldown = 0.0

    glutPostRedisplay() 

def init():
    global last_frame_time
    glClearColor(0, 0, 0, 1)
    gluOrtho2D(0, window_width, 0, window_height)
    last_frame_time = time.time()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Catch the Diamonds!")
    init()
    glutDisplayFunc(display)
    glutSpecialFunc(keyboard_special_down)
    glutMouseFunc(mouse_click)
    glutIdleFunc(idle)
    reset_game()
    glutMainLoop()

if __name__ == "__main__":
    main()
