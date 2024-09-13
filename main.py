import cv2
import mediapipe as mp
import numpy as np
import pygame
from random import randint, uniform
from time import sleep
import asyncio
import sys
from hangul import eng2kor,kor2eng

fruits = ["감", "두리안", "딸기", "레몬", "메론", "바나나", "배", "복숭아", "블루베리", "사과", "산딸기", "샤인머스켓", "수박", "오렌지", "용과", "참외", "청사과", "체리", "파인애플", "포도"]
fruit_score = {
    "감":1,
    "두리안":2,
    "딸기":1,
    "레몬":2,
    "메론":3,
    "바나나":2,
    "배":1,
    "복숭아":1,
    "블루베리":1,
    "사과":1,
    "산딸기":1,
    "샤인머스켓":2,
    "수박":3,
    "오렌지":1,
    "용과":4,
    "참외":1,
    "청사과":2,
    "체리":1,
    "파인애플":4,
    "포도":1
}

fruit_rect = {}

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_drawing_styles = mp.solutions.drawing_styles

l_circles = []
r_circles = []
counter = 0
cap = cv2.VideoCapture(1)
left, right = (0,0), (0,0)

## 상수

SCREEN_X = 1000

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Fruit Slicing")
s_w, s_h = pygame.display.get_surface().get_size()
font = pygame.font.SysFont("malgungothic", 40)
ranking_font = pygame.font.SysFont("malgungothic", 27)
score_font = pygame.font.SysFont("malgungothic", 80)
countdown_font = pygame.font.SysFont("malgungothic", 200)
slash = pygame.mixer.Sound( "./asset/slash.mp3" )
explosion = pygame.mixer.Sound( "./asset/bomb.mp3" )
fruit_img = {}
fruit_imgL = {}
fruit_imgR = {}
bomb_image = pygame.transform.scale(pygame.image.load("./asset/폭탄.png"), (150, 150))
explosions = [ pygame.transform.scale(pygame.image.load(f"./asset/explosion{i}.png"),(230,230)) for i in range(1, 4) ]
transparent = pygame.transform.scale(pygame.image.load("./asset/transparent.png").convert_alpha(), (300, 300))
GAME_OVER = pygame.image.load("./asset/game_over.png")
TEXZT_INPUT = pygame.image.load("./asset/text_input.png")

for fruit in fruits:
    _transparent = transparent.copy()
    _transparent.blit(pygame.image.load(f"./asset/{fruit}.png"), (0,0))#pygame.transform.scale(pygame.image.load(f"./asset/{fruit}.png"), (150,150)), (0,0))
    fruit_img[fruit] = _transparent
    
    fruit_imgL[fruit] = pygame.image.load(f"./asset/{fruit}L.png")
    fruit_imgR[fruit] = pygame.image.load(f"./asset/{fruit}R.png")

score = 0
timer = 0
leaderBoard = {}

def choose_fruit():
    random = randint(0, 19)
    return fruits[random]

def collide(circle_pos, circle_radius, rect):
    circle_x, circle_y = circle_pos
    rect_x, rect_y, rect_width, rect_height = rect
    nearest_x = max(rect_x, min(circle_x, rect_x + rect_width))
    nearest_y = max(rect_y, min(circle_y, rect_y + rect_height))
    distance_x = circle_x - nearest_x
    distance_y = circle_y - nearest_y
    distance_squared = distance_x ** 2 + distance_y ** 2
    return distance_squared <= circle_radius ** 2

fruit_rect_subsurface = pygame.Rect(0, 0, 200, 200)

def real_image(image):
    result = image.subsurface((fruit_rect_subsurface)).get_rect()
    return result
for name, img in fruit_img.items():
    fruit_rect[name] = real_image(img)

class Fruit(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.rotation = randint(-60, 60)
        self.image = pygame.transform.rotate(fruit_img[name], self.rotation)
        self.rect = self.image.get_rect()
        self.rect.x = randint(0, SCREEN_X)
        self.rect.y = s_h
        self.score = fruit_score[name]

        self.direction = -1
        self.x_speed = uniform(0, 3) * 1 if randint(0, 1) else -1
        self.y_speed = uniform(30, 50)
        # self.score = score_dict[name]
        self.is_slashed = False
        self.slashing_count = 0
        self.angle = 0
        
    def fruit_slashing(self):
        left = fruit_imgL[self.name]
        right = fruit_imgR[self.name]
        # w, h = left.get_size()[0]+right.get_size()[0], left.get_size()[1]+right.get_size()[1]
        result = transparent.copy()
        
        left = pygame.transform.rotate(left, self.angle)
        right = pygame.transform.rotate(right, -self.angle)
        result.blit(left, (0, 0))
        result.blit(right, (left.get_size()[0], 0))
        # result = pygame.transform.rotate(result, self.rotation)
        
        return result

    def slashed(self):
        if self.is_slashed: return
        
        global score
        score += self.score
        slash.play()
        self.is_slashed = True

    def update(self):
        if self.is_slashed and self.slashing_count <= 36:
            self.image = pygame.transform.rotate(self.fruit_slashing(), self.rotation)
            self.rect = self.image.get_rect(center=self.rect.center)
            self.slashing_count += 1
            self.angle += 1
            
        self.rect.x += self.x_speed
        self.y_speed += self.direction * 1.5
        self.rect.y += self.direction * (self.y_speed)
        if self.y_speed <= 0:
            self.direction = 1
        if self.rect.y >= s_h+80:
            self.kill()

class Bomb(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = bomb_image
        self.rect = self.image.get_rect()
        self.rect.x = randint(0, SCREEN_X)
        self.rect.y = s_h

        self.direction = -1
        self.x_speed = uniform(0, 3) * 1 if randint(0, 1) else -1
        self.y_speed = uniform(30, 50)

    def slashed(self):
        global score
        screen.blit(explosions[randint(0,2)], (self.rect.x, self.rect.y))
        explosion.play()
        decrease = randint(10,30)
        if score - decrease < 0:
            score = 0
        else:
            score -= decrease
        
        self.kill()
    def update(self):
        self.rect.x += self.x_speed
        self.y_speed += self.direction * 1.5
        self.rect.y += self.direction * (self.y_speed)
        if self.y_speed <= 0:
            self.direction = 1
        if self.rect.y >= s_h+80:
            self.kill()


async def save():
    with open("./ranking.txt", "w") as ranking:
        ranking.write("\n".join([ f"{k}:{v}" for k, v in rankings.items()]))

INTERFACE = pygame.image.load("./asset/interface.png")
INTERFACE = pygame.transform.scale(INTERFACE, (s_w, s_h))

game = True
sprite_group = pygame.sprite.Group()

clock = pygame.time.Clock()
rankings = {}
with open("./ranking.txt", "r") as ranking:
    for i in ranking.readlines():
        print(i[(i.index(":")+1):-1])
        rankings[i[:i.index(":")]] = int(i[(i.index(":")+1):-1])   
    
countdown = 3

async def counting():
    global countdown
    for i in range(3):
        await asyncio.sleep(1.0)
        countdown -= 1

with mp_pose.Pose(min_detection_confidence=0.41,
                  min_tracking_confidence=0.7,
                  model_complexity=1) as pose: 
    clock.tick(240)
    while game:
        timer = 0
        score = 0
        pan = True
        countdown = 3
        countdownTime = pygame.time.get_ticks()
        while countdown:
            if pygame.time.get_ticks() - countdownTime >= 1000:
                countdownTime = pygame.time.get_ticks()
                countdown -= 1
            _, frame = cap.read()
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (s_w, s_h))
            frame = frame.swapaxes(0,1)
            frame = cv2.flip(frame, 0)
            frame = pygame.surfarray.make_surface(frame)
            screen.blit(frame, (0,0))
            screen.blit(INTERFACE, (0,0))
            screen.blit(countdown_font.render(str(countdown)+"초", True, (0,0,0)), (s_w/2-200, s_h/2-150
                                                                                   ))
            pygame.display.update()
        start_ticks = next_ticks = pygame.time.get_ticks()
        while timer <= 30 and pan:
            _, frame = cap.read()
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
                        
            try:
                results = pose.process(image)
                left = (s_w-results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_INDEX].x*s_w, results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_INDEX].y*s_h)
                right = (s_w-results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_INDEX].x*s_w, results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_INDEX].y*s_h)
            except: pass
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (s_w, s_h))
            frame = frame.swapaxes(0,1)
            frame = cv2.flip(frame, 0)
            frame = pygame.surfarray.make_surface(frame)
            screen.blit(frame, (0,0))

            if pygame.time.get_ticks() >= next_ticks:
                for i in range(randint(1, 3)):
                    fruit = Fruit(choose_fruit())
                    sprite_group.add(fruit)
                
                if randint(1, 5) == 1:
                    bomb = Bomb()
                    sprite_group.add(bomb)
                    
                next_ticks += randint(900, 2500)
            sprite_group.update()
            sprite_group.draw(screen)

            pygame.draw.circle(screen,pygame.Color(75, 178, 255),(left[0],left[1]),20)
            pygame.draw.circle(screen,pygame.Color(5, 241, 245),(left[0],left[1]),10)
            pygame.draw.circle(screen,pygame.Color(75, 178, 255),(right[0],right[1]),20)
            pygame.draw.circle(screen,pygame.Color(5, 241, 245),(right[0],right[1]),10)
            
            l_circles.append((pygame.Color(75, 178, 255),(left[0],left[1]),20))
            l_circles.append((pygame.Color(5, 241, 245),(left[0],left[1]),10))
            r_circles.append((pygame.Color(75, 178, 255),(right[0],right[1]),20))
            r_circles.append((pygame.Color(5, 241, 245),(right[0],right[1]),10))

            if counter == 3: 
                l_circles = l_circles[2:]
                r_circles = r_circles[2:]
            else: counter += 1

            prev = []

            for index, circle in enumerate(l_circles):
                pygame.draw.circle(screen, circle[0], circle[1], circle[2])
                if index != 0 and index & 1 == 0:
                    pygame.draw.line(screen, pygame.Color(75, 178, 255), prev[1], circle[1], 45)
                    pygame.draw.line(screen, pygame.Color(5, 241, 245), prev[1], circle[1], 25)
                prev = circle

            for index, circle in enumerate(r_circles):
                pygame.draw.circle(screen, circle[0], circle[1], circle[2])
                if index != 0 and index & 1 == 0:
                    pygame.draw.line(screen, pygame.Color(75, 178, 255), prev[1], circle[1], 45)
                    pygame.draw.line(screen, pygame.Color(5, 241, 245), prev[1], circle[1], 25)
                prev = circle
            screen.blit(INTERFACE, (0,0))
            
            count = 0
            for k, v in sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:3]:
                text = ranking_font.render(f"{k} {v}점", 255, True)
                screen.blit(text, (1385, 135+count*80))
                count += 1
            count = 0
            for k, v in sorted(rankings.items(), key=lambda x: x[1], reverse=True)[3:11]:
                text = ranking_font.render(f"{k} {v}점", 255, True)
                screen.blit(text, (1385, 375+count*49))
                count += 1

            for sprite in sprite_group:
                rect = fruit_rect[fruit.name]
                rect.x = sprite.rect.x
                rect.y = sprite.rect.y
                if collide((left[0], left[1]),35, rect) or collide((right[0], right[1]),10, rect):
                    sprite.slashed()
            clock.tick()

                
            print(clock.get_fps())

            timer = (pygame.time.get_ticks() - start_ticks) / 1000
            timerText = font.render("{0:>2}초".format(str(round(30-timer))), True, (255,255,255))
            scoreText = font.render("{0:>2}점".format(score), True, (255,255,255))
            screen.blit(timerText, (756, 33))
            screen.blit(scoreText, (1085, 33))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SEMICOLON:
                        pan = False
                    elif event.key == pygame.K_PERIOD:
                        asyncio.run(save())
                        sys.exit(0)
        input_not_end = True
        screen.blit(GAME_OVER, (s_w/2-350, s_h/2-120))
        name = ""
        while input_not_end:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        input_not_end = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        name += event.unicode
            screen.blit(INTERFACE, (0,0))
            count = 0
            for k, v in sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:3]:
                text = ranking_font.render(f"{k} {v}점", 255, True)
                screen.blit(text, (1385, 135+count*80))
                count += 1
            count = 0
            for k, v in sorted(rankings.items(), key=lambda x: x[1], reverse=True)[3:10]:
                text = ranking_font.render(f"{k} {v}점", 255, True)
                screen.blit(text, (1385, 375+count*49))
                count += 1
            name = eng2kor(kor2eng(name))
            scoreText = score_font.render("{0:>2}점".format(str(score)), True, (0,0,0))
            nameText = font.render(name, True,(0,0,0))
            screen.blit(GAME_OVER, (s_w/2-350, s_h/2-120))
            screen.blit(scoreText, (750, 450))
            screen.blit(nameText, (700, 580))
            pygame.display.update()
        rankings[name] = score
pygame.quit()
