
# Task 1
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math
import random

W_Width, W_Height = 500,500

speed = 0.01
create_new = False
raindrops = []
rain_angle = 0  
sky_brightness = 0.0  
RAIN_COUNT = 100
RAIN_SPEED = 0.5
is_day = True

class point:
    def __init__(self):
        self.x=0
        self.y=0
        self.z=0


def crossProduct(a, b):
    result=point()
    result.x = a.y * b.z - a.z * b.y
    result.y = a.z * b.x - a.x * b.z
    result.z = a.x * b.y - a.y * b.x

    return result

def convert_coordinate(x,y):
    global W_Width, W_Height
    a = x - (W_Width/2)
    b = (W_Height/2) - y 
    return a,b

def drawTrees():
    glBegin(GL_TRIANGLES)
    for i in range(-500, 500, 30):
        glColor3f(0, 1, 0)
        glVertex2f(i, 0)
        glVertex2f(i + 15, 40)
        glVertex2f(i + 30, 0)
    glEnd()


def drawHouse():
    glBegin(GL_TRIANGLES)
    glColor3f(0.97, 0.98, 0.9)
    glVertex2f(-500, 0)
    glVertex2f(-10000, -10000)
    glVertex2f(1000, 0)
    glEnd()
    
    glBegin(GL_TRIANGLES)
    glColor3f(0.5, 0.0, 1.0)
    glVertex2f(-80, 0)
    glVertex2f(0, 60)
    glVertex2f(80, 0)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(1, 0.25, 0.2)
    glVertex2f(-80, 0)
    glVertex2f(-80, -80)
    glVertex2f(80, 0)

    glVertex2f(-80, -80)
    glVertex2f(80, 0)
    glVertex2f(80, -80)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(0.1, 0.5, 1.0)
    glVertex2f(-15, -80)
    glVertex2f(-15, -30)
    glVertex2f(15, -30)

    glVertex2f(-15, -80)
    glVertex2f(15, -30)
    glVertex2f(15, -80)
    glEnd()
   
def drawRain():
    glColor3f(0.8, 0.8, 1.0)
    glLineWidth(2)
    glBegin(GL_LINES)
    for drop in raindrops:
        x, y = drop
        glVertex2f(x, y)
        glVertex2f(x + rain_angle * 5, y - 10)
        
    glEnd()

def drawShapes():
    drawTrees()
    drawHouse()
    drawRain()
    

def keyboardListener(key, x, y):
    global is_day
    if key == b'd':
        is_day = not is_day
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global speed, rain_angle
    global sky_brightness
    if key == GLUT_KEY_LEFT:
        rain_angle -= 0.2 
    elif key == GLUT_KEY_RIGHT:
        rain_angle += 0.2 
    
    glutPostRedisplay()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(sky_brightness, sky_brightness, sky_brightness, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 0, 300, 0, 0, 0, 0, 1, 0)

 
    drawShapes()

    glutSwapBuffers()

def animate():
    
    global raindrops, rain_angle, sky_brightness

    for drop in raindrops:
        drop[0] += rain_angle * 0.5
        drop[1] -= RAIN_SPEED
        if drop[1] < -500:
            drop[0] = random.uniform(-500, 500)
            drop[1] = random.uniform(500, 500)
    if is_day and sky_brightness < 1.0:
        sky_brightness += 0.0005 
    elif not is_day and sky_brightness > 0.0:
        sky_brightness -= 0.0005 

    sky_brightness = max(0.0, min(1.0, sky_brightness)) 

    glutPostRedisplay()

def init():
    glClearColor(0,0,0,0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(104,	1,	1,	1000.0)
  
    global raindrops
    for _ in range(RAIN_COUNT):
        raindrops.append([random.uniform(-500, 500), random.uniform(-500,500)])

glutInit()
glutInitWindowSize(W_Width, W_Height)
glutInitWindowPosition(0, 0)
glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB) 
wind = glutCreateWindow(b"OpenGL Coding Practice")
init()

glutDisplayFunc(display)	
glutIdleFunc(animate)	
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)

glutMainLoop()		


