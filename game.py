import pygame
import os   # To get control over files and folders
import random
pygame.init()
pygame.mixer.init()     # Initializing for adding music 

# Display
screen_width=900
screen_height=int(screen_width*0.8)
display=pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Code of Death")

# Clock
clock=pygame.time.Clock()
fps=60

# Music
pygame.mixer.music.load("audio/outlaw.mp3")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1,fade_ms=4000,start=9)
jump_sound=pygame.mixer.Sound("audio/jump.wav")
click_sound=pygame.mixer.Sound("audio/click.mp3")
shoot_sound=pygame.mixer.Sound("audio/shot.wav")
explosion_sound=pygame.mixer.Sound("audio/grenade.wav")
death_sound=pygame.mixer.Sound("audio/death.mp3")

# Game Variables
GRAVITY=0.5    # Gravity
ROWS=16
COLS=150
TILE_SIZE=screen_height//ROWS
TILE_TYPES=21
SCROLL_THRESHOLD=200
LEVEL=1
MAX_LEVEL=4
background_scrolled=0

# Loading images
    # Buttons images
exit_img=pygame.image.load("image/exit_btn.png").convert_alpha()
restart_img=pygame.image.load("image/restart_btn.png").convert_alpha()
start_img=pygame.image.load("image/start_btn.png").convert_alpha()
controls_img=pygame.image.load("image/controls_btn.png").convert_alpha()
controls_menu_img=pygame.image.load("image/controls_menu.png").convert_alpha()
controls_menu_img=pygame.transform.scale(controls_menu_img,(700,575))

    # Background images
homescreen_img=pygame.image.load("image/background/homescreen.jpg").convert_alpha()
title_img=pygame.image.load("image/title.png").convert_alpha()
title_img=pygame.transform.scale(title_img,(screen_width*0.45,screen_height*0.18))

mountain_img=pygame.image.load("image/background/mountain.png").convert_alpha()
pine1_img=pygame.image.load("image/background/pine1.png").convert_alpha()
pine2_img=pygame.image.load("image/background/pine2.png").convert_alpha()
cloud_img=pygame.image.load("image/background/sky_cloud.png").convert_alpha()

def draw_background():
    width=cloud_img.get_width()
    for i in range(5):      # Ensuring that background covers the whole game
        display.blit(cloud_img,(width*i-background_scrolled*0.5,-50))
        display.blit(mountain_img,(width*i-background_scrolled*0.7,screen_height-mountain_img.get_height()-350))
        display.blit(pine1_img,(width*i-background_scrolled*0.8,screen_height-pine1_img.get_height()-180))
        display.blit(pine2_img,(width*i-background_scrolled*0.9,screen_height-pine2_img.get_height()))
    # Displaying world elements
    world.draw(world.obstacle_lst)
    world.draw(world.decoration_lst)
    world.draw(world.water_lst)
    world.draw(world.exit_lst)

    # Loading grid images
grid_img_list=[]       
for i in range(TILE_TYPES):
    img=pygame.image.load(f"image/tile/{i}.png")
    img=pygame.transform.scale(img,(TILE_SIZE,TILE_SIZE))
    grid_img_list.append(img)

# Loading levels
def load_leveldata():
    world_data=[]
    with open(f"levels/level{LEVEL}_data.csv","r") as level_data:
        for row in level_data:
            values_list=row.strip().split(",")
            world_data.append(values_list)
    return world_data 

# Fonts
def show_text(text,color,x,y,font_size=30):
    font=pygame.font.SysFont(None,font_size)  # Font
    output_text=font.render(text,True,color)
    display.blit(output_text,(x,y))

# Reset Game
def reset_game():
    bullets_group.empty()
    grenades_group.empty()
    explosion_group.empty()
    item_group.empty()

    creature_list.clear()
    world.obstacle_lst.clear()
    world.decoration_lst.clear()
    world.water_lst.clear()
    world.exit_lst.clear()

    

class Soldier(pygame.sprite.Sprite):
    def __init__(self,soldier_type,soldier_x,soldier_y,scale):
        pygame.sprite.Sprite.__init__(self)
        # Moving variables
        self.aliv=True
        self.soldier_type=soldier_type
        self.moving_left=False
        self.moving_right=False
        self.jump=False
        self.in_air=True
        self.vel_y=0
        self.flip=False    # Flipping the direction of soldier (for left arrow)
        self.direction=1    # 1 denotes right direction and -1 denotes left direction (Use in bullet direction)  
        self.last_updated=pygame.time.get_ticks()
        self.animation_dict={"Idle":[],"Run":[],"Jump":[],"Death":[]}
        soldier_states=list(self.animation_dict.keys())
        self.__fill_animation_dict(soldier_type,scale,soldier_states)
        self.rect=self.img.get_rect()
        self.rect.x=soldier_x
        self.rect.y=soldier_y
        self.animation_index=0    # Animation number to show at a particular time
        self.soldier_state="Idle"
        self.shoot=False
        self.nextShoot_time=0    # Controlling the time of next bullet loading
        self.ammo=20
        self.health=100
        self.max_health=100
        self.throw_grenade=False
        self.grenade_thrown=False
        self.grenade=5
        self.scroll=0
        # AI specific variables
        self.move_counter=0     # Trace how many times enemy has moved
        self.idle=False        # Specifing whether the state of enemy is idle or Running
        self.idle_time=100
        self.shoot_rect=pygame.Rect(self.rect.centerx+20,self.rect.centery,150,20)    # Vision upto which enemy can detect the soldier

    def draw(self):
        display.blit(pygame.transform.flip(self.img,self.flip,False),(self.rect.x,self.rect.y))

    def move(self,speed):
        dx=0       # Change in x-position of each iteration of gameloop
        dy=0       # Change in y-position of each iteration of gameloop
        # self.scroll=0
        if self.moving_left and self.aliv:
            dx=-speed
            self.flip=True
            self.direction=-1

        if self.moving_right and self.aliv:
            dx=speed
            self.flip=False
            self.direction=1

        if self.jump and self.in_air==False:   # Jump only when not in air
            self.vel_y-=11
            self.jump=False
            self.in_air=True
            jump_sound.play()

        self.vel_y+=GRAVITY
        if self.vel_y >9:    # Controlling the impact of gravity
            self.vel_y=9
        dy=self.vel_y

        # Collision checking
        if self.soldier_type=="player":
            if self.rect.x+dx < 0 or self.rect.x+dx > screen_width:      # with screen
                dx=0
            if self.rect.bottom > screen_height:
                self.health=0

        for tile in world.obstacle_lst:       # with tiles
            if tile[1].colliderect(self.rect.x+dx,self.rect.y,self.rect.width-20,self.rect.height):    # x-direction
                dx=0
                # If enemy collides with tiles
                # if self.soldier_type=="enemy":
                #     self.direction*=-1
                #     self.move_counter=0
            if tile[1].colliderect(self.rect.x,self.rect.y+dy,self.rect.width-20,self.rect.height):    # y-direction
                if self.vel_y<0:     # in Air 
                    self.vel_y=0
                    dy=tile[1].bottom-self.rect.top
                else:                # on Ground
                    self.vel_y=0    
                    self.in_air=False
                    dy=tile[1].top-self.rect.bottom
        self.rect.x+=dx
        self.rect.y+=dy

        # Scrolling
        if self.soldier_type=="player":     # For Player movement only
            if (self.rect.right > screen_width-SCROLL_THRESHOLD and background_scrolled+screen_width < COLS*TILE_SIZE) or (self.rect.left<SCROLL_THRESHOLD and background_scrolled > 0):    # Check if player crosses the threshold to start scrolling 
                self.rect.x-=dx     # Player will stay at his position
                self.scroll=-dx     # and the world starts moving
            else:
                self.scroll=0

    def __fill_animation_dict(self,soldier_type,scale,soldier_states):
        for i in soldier_states:    # Traversing each soldier_state
            no_of_images=len(os.listdir(f"image/{soldier_type}/{i}"))
            for j in range(no_of_images):     # Traversing each image in the ith soldier_state
                img=pygame.image.load(f"image/{soldier_type}/{i}/{j}.png")
                self.img=pygame.transform.scale(img,(int(img.get_width()*scale),int(img.get_height()*scale))).convert_alpha()
                self.animation_dict[i].append(self.img)
    
    def update_animation(self):
        change_time=120   # in millliseconds
        self.img=self.animation_dict[self.soldier_state][self.animation_index]    # Setting which image to show at particular instance
        if pygame.time.get_ticks()-self.last_updated>change_time:     # Checking certain time to pass out
            self.last_updated=pygame.time.get_ticks()
            self.animation_index+=1     # Pointing to next image
            if self.animation_index==len(self.animation_dict[self.soldier_state]):    # Checking image list end
                if self.soldier_state=="Death":
                    self.animation_index=len(self.animation_dict[self.soldier_state])-1   # Fixing animation as last one
                    self.kill()
                else: 
                    self.animation_index=0   # Reset to animation from 1st image

    def update_state(self,new_state):
        if self.soldier_state!=new_state:
            self.soldier_state=new_state
            self.animation_index=0
            self.last_updated=pygame.time.get_ticks()

    def shootout(self):
        if self.nextShoot_time==0 and self.ammo:
            bullet1=Bullet(self.rect.centerx + (self.rect.size[0]/2 +9)*self.direction,self.rect.centery,self.direction)
            bullets_group.add(bullet1)
            self.nextShoot_time=20
            self.ammo-=1     # Reducing the number of bullets left
            shoot_sound.play()
    
    def is_alive(self):
        if self.health<=0:
            self.health=0
            self.aliv=False
            self.update_state("Death")
            if self.soldier_type=="player":
                death_sound.play()
                pygame.mixer.music.stop()

    
    def grenade_throwout(self):
        if self.grenade_thrown==False and self.grenade>0:
            grenade1=Grenade(self.rect.centerx + (self.rect.size[0]/2 +5)*self.direction,self.rect.top,self.direction)
            grenades_group.add(grenade1)
            self.grenade_thrown=True
            self.grenade-=1

    def ai(self,soldier1):     # For Enemies
        self.rect.x+=soldier1.scroll       #Scrolling
        if self.aliv and soldier1.aliv:
            self.shoot_rect.centerx+=soldier1.scroll
            if self.shoot_rect.colliderect(soldier1.rect):     # Checking if soldier come in shoot_rect range
                self.idle=True
                self.update_state("Idle")
                self.shoot=True
                self.shootout()
            else:
                # self.idle=False
                self.shoot=False
            if self.idle==False:           
                if random.randint(0,100)==10:
                    self.idle=True
                self.update_state("Run")     # Changing the state of enemy to Run
                # Fixing moving position of enemy
                if self.direction==1:
                    self.moving_right=True
                    self.moving_left=False
                else:
                    self.moving_left=True
                    self.moving_right=False
                self.move(2)      # Moving the enemy
                self.shoot_rect.center=(self.rect.centerx+105*self.direction,self.rect.centery)     # Updating shot_rect position according to the position of the enemy
                self.move_counter+=1

                if self.move_counter>TILE_SIZE*1.2:     # Setting maximum distance to travel for enemy
                    self.direction*=-1      # Changing the direction after the distance travelled
                    self.move_counter*=-1
                
            else:
                self.update_state("Idle")
                self.idle_time-=1
                if self.idle_time==0:
                    self.idle=False
                    self.idle_time=100

            # Drawing healthbar
            self.draw_healthbar(self.rect.x-5,self.rect.y-15,width_scale=0.5,height_scale=0.7)
                    
            
    def draw_healthbar(self,x,y,width_scale=1,height_scale=1):
        pygame.draw.rect(display,"black",(x-2,y-2,(self.max_health*1.5+4)*width_scale,(20+4)*height_scale))     # Making boundry of health bar        
        pygame.draw.rect(display,"red",(x,y,self.max_health*1.5*width_scale,20*height_scale))      
        pygame.draw.rect(display,"green",(x,y,self.health*1.5*width_scale,20*height_scale))  



class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y,direction):
        pygame.sprite.Sprite.__init__(self)
        self.image=pygame.image.load("image/icons/bullet.png")
        self.rect=self.image.get_rect()
        self.rect.center=(x,y)
        self.speed=20
        self.direction=direction

    # bullet_group function overloading
    def update(self,creature_list):
        # self.rect.x+=Soldier1.scroll       #Scrolling
        self.rect.x+=self.speed * self.direction
        # Checking collision of bullet with screen
        if self.rect.left>screen_width or self.rect.right<0:
            self.kill()
        # Checking the collision of bullet 
        if pygame.sprite.spritecollide(creature_list[0],bullets_group,False):     # with Player
            if creature_list[0].aliv:
                self.kill()
                creature_list[0].health-=10

        for i in range(1,len(creature_list)):
            if pygame.sprite.spritecollide(creature_list[i],bullets_group,False):     # with another soldier
                if creature_list[i].aliv:
                    self.kill()
                    creature_list[i].health-=30

        for tile in world.obstacle_lst:
            if tile[1].colliderect(self.rect):     # with tiles
                self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__(self,x,y,direction):
        pygame.sprite.Sprite.__init__(self)
        self.image=pygame.image.load("image/icons/grenade.png")
        self.rect=self.image.get_rect()
        self.rect.center=(x,y)
        self.vel_y=-10
        self.vel_x=7
        self.direction=direction
        self.timer=100


    def update(self,creature_list):
        self.rect.x+=Soldier1.scroll       #Scrolling
        self.vel_y+=GRAVITY    # Impact of gravity
        # Instantaneous Velocity
        dx = self.vel_x*self.direction
        dy = self.vel_y

		#check for collision with level
        for tile in world.obstacle_lst:
            #check collision with walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                self.direction *= -1
                dx = self.direction * self.vel_x
            #check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                self.vel_x = 0
                #check if below the ground, i.e. thrown up
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom	
        self.rect.x+=dx
        self.rect.y+=dy

        self.timer-=1
        if self.timer==0:      # Checking for explosion
            explosion=Explosion(self.rect.x,self.rect.y)
            explosion_group.add(explosion)
            explosion_sound.play()
            self.kill()    # Kill grenade after the explosion

            # Decreasing the health of soldiers after explosion
            for explosion_impact in range(1,3):      # Explosion impact will be more if soldier is closer to grenade
                if abs(self.rect.centerx - creature_list[0].rect.centerx) <=TILE_SIZE*explosion_impact*0.8 and abs(self.rect.centery - creature_list[0].rect.centery) <=TILE_SIZE*explosion_impact*0.8:
                    creature_list[0].health-=25     # Reducing health of the player

                for i in range(1,len(creature_list)):     # For Enemy
                    if abs(self.rect.centerx - creature_list[i].rect.centerx) <=TILE_SIZE*explosion_impact*0.8 and abs(self.rect.centery - creature_list[i].rect.centery) <=TILE_SIZE*explosion_impact*0.8:
                        creature_list[i].health-=50      # Reducing health of the enemy





class Explosion(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.images_list=[]
        for i in range(1,6):
            self.image=pygame.image.load(f"image/explosion/exp{i}.png").convert_alpha()
            self.images_list.append(self.image)
        self.rect=self.image.get_rect()
        self.rect.center=(x,y)
        self.animation_index=0
        self.animation_changetime=8

    def update(self):
        self.rect.x+=Soldier1.scroll       #Scrolling
        self.image=self.images_list[self.animation_index]
        if self.animation_changetime==0:
            self.animation_index+=1
            if self.animation_index==len(self.images_list):
                self.kill()

        else:
            self.animation_changetime-=1

        
class Item_Box(pygame.sprite.Sprite):
    def __init__(self,item_type,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image=pygame.image.load(f"image/icons/{item_type}_box.png").convert_alpha()
        self.rect=self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))    # Since size of item <size of tile
        self.item_type=item_type


    def update(self):
        self.rect.x+=Soldier1.scroll       #Scrolling
        if pygame.sprite.collide_rect(Soldier1,self):
            self.kill()
            if self.item_type=="health":
                Soldier1.health+=30
                if Soldier1.health>Soldier1.max_health:
                    Soldier1.health=Soldier1.max_health
            
            if self.item_type=="ammo":
                Soldier1.ammo+=10
                if Soldier1.ammo>20:
                    Soldier1.ammo=20
                
            if self.item_type=="grenade":
                Soldier1.grenade+=3
                if Soldier1.grenade>5:
                    Soldier1.grenade=5

class World():
    def __init__(self,world_data):
        self.obstacle_lst=[]
        self.decoration_lst=[]
        self.water_lst=[]
        self.exit_lst=[]
        self.world_data=world_data
        self.process_grid()

    def process_grid(self):
        for i,row in enumerate(self.world_data):
            for j,tile in enumerate(row):
                tile=int(tile)
                if tile>=0:
                    tile_img=grid_img_list[tile]
                    tile_img_rect=tile_img.get_rect()
                    tile_img_rect.x=j*TILE_SIZE
                    tile_img_rect.y=i*TILE_SIZE
                    tile_data=(tile_img,tile_img_rect)

                    if tile<=8:     #  tiles
                        self.obstacle_lst.append(tile_data)
                    elif tile<=10:      # Water
                        self.water_lst.append(tile_data)

                    elif tile<=14:     # Decoration
                        self.decoration_lst.append(tile_data)

                    elif tile==15:
                        Soldier1=Soldier("player",tile_img_rect.x,tile_img_rect.y,1.65)
                        creature_list.insert(0,Soldier1)

                    elif tile==16:
                        Enemy=Soldier("enemy",tile_img_rect.x,tile_img_rect.y,1.7)
                        creature_list.append(Enemy)

                    elif tile==17:
                        ammo_box=Item_Box("ammo",tile_img_rect.x,tile_img_rect.y)
                        item_group.add(ammo_box)
                    elif tile==18:
                        grenade_box=Item_Box("grenade",tile_img_rect.x,tile_img_rect.y)
                        item_group.add(grenade_box)    
                    elif tile==19:
                        health_box=Item_Box("health",tile_img_rect.x,tile_img_rect.y)
                        item_group.add(health_box)
                    elif tile==20:     # Next level
                        self.exit_lst.append(tile_data)
    
    def draw(self,list):
        for tile_data in list:
            tile_data[1].x+=Soldier1.scroll
            display.blit(tile_data[0],tile_data[1])

    def water(self):
        for water_data in self.water_lst:
                if water_data[1].colliderect(Soldier1.rect):
                    Soldier1.health=0


    def exit(self):
        global Soldier1

        for exit_data in self.exit_lst:
            if exit_data[1].colliderect(Soldier1.rect):
                for enemy in creature_list[1:]:
                    if enemy.aliv:
                        break
                else:
                    global LEVEL
                    global background_scrolled
                    global world
                    LEVEL+=1
                    background_scrolled=0
                    reset_game()
                    if LEVEL<=MAX_LEVEL:
                        world=World(load_leveldata())
                        Soldier1=creature_list[0]
                        

        
class Button():
	def __init__(self,x, y, image, scale):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self):
		action = False
		#get mouse position
		pos = pygame.mouse.get_pos()
		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		display.blit(self.image, (self.rect.x, self.rect.y))
		return action


creature_list=[] 

# buttons Creation
start_button=Button(screen_width*0.3,screen_height*0.6,start_img,1)
exit_button=Button(screen_width*0.32,screen_height*0.8,exit_img,1)
exit_inloop_button=Button(screen_width*0.45,screen_height*0.6,exit_img,0.7)
restart_button=Button(screen_width*0.41,screen_height*0.4,restart_img,2)
controls_button=Button(screen_width*0.75,screen_height*0.93,controls_img,0.4)

# Sprite Groups
bullets_group=pygame.sprite.Group()
grenades_group=pygame.sprite.Group()
explosion_group=pygame.sprite.Group()
item_group=pygame.sprite.Group()

# Creating some objects
world=World(load_leveldata())
Soldier1=creature_list[0]



# Gameloop
def gameloop():
    global background_scrolled
    global world
    global Soldier1

    # Gameloop variables
    exit_game=False
    game_over=False

    # Images
    grenade_img=pygame.image.load("image/icons/grenade.png")
    bullet_img=pygame.image.load("image/icons/bullet.png")
    

    # Gameloop starts
    while exit_game==False:
        if Soldier1.aliv==False:
            game_over=True

        if game_over:
            draw_background()
            Soldier1.vel_y=0.8
            Soldier1.move(7)
            for creature in creature_list:
                creature.update_animation()
                creature.draw()
            
            if restart_button.draw():
                click_sound.play()
                game_over=False
                background_scrolled=0
                reset_game()
                world=World(load_leveldata())
                Soldier1=creature_list[0]
                pygame.mixer.music.play(-1)

            if exit_inloop_button.draw():
                exit_game=True


        else:
            world.water()
            world.exit()
            draw_background()

            for creature in creature_list:
                creature.is_alive()
                creature.update_animation()
                creature.draw()
                if creature.nextShoot_time>0:       # Shoot time updation
                    creature.nextShoot_time-=1
            Soldier1.move(7)       # Handling keyboard events
            background_scrolled-=Soldier1.scroll     # Total background scrolled

            for enemy in creature_list[1:]:     
                enemy.ai(Soldier1)          # Calling ai for enemies

            # Functions present in sprite class
            bullets_group.update(creature_list)     # Overloaded function to update position of bullet, Checking collision
            grenades_group.update(creature_list)
            explosion_group.update()
            item_group.update()
            bullets_group.draw(display)
            grenades_group.draw(display)
            explosion_group.draw(display)
            item_group.draw(display)

            # Representing some attributes of player and level info
            show_text("Health : ","red",20,10)
            Soldier1.draw_healthbar(101,10)

            show_text("Ammo : ","red",20,40)
            for i in range(Soldier1.ammo):
                display.blit(bullet_img,(97+i*10,45))
            
            show_text("Grenade : ","red",20,70)
            for i in range(Soldier1.grenade):
                display.blit(grenade_img,(120+i*15,73))

            show_text("LEVEL- "+str(LEVEL),"#420007",410,5,40)

        # Updating state of Soldier according to key pressed
        if Soldier1.aliv:
            if Soldier1.shoot:
                Soldier1.shootout()
            elif Soldier1.throw_grenade:
                Soldier1.grenade_throwout()
            if Soldier1.moving_left or Soldier1.moving_right:
                Soldier1.update_state("Run")
            elif Soldier1.in_air:
                Soldier1.update_state("Jump")
            else:
                Soldier1.update_state("Idle")

        # Events Handling
        for event in pygame.event.get():
            # Quit Game
            if event.type==pygame.QUIT:
                exit_game=True
            
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_LEFT:
                    Soldier1.moving_left=True
                if event.key==pygame.K_RIGHT:
                    Soldier1.moving_right=True
                if event.key==pygame.K_UP and Soldier1.aliv:
                    Soldier1.jump=True
                if event.key==pygame.K_SPACE and Soldier1.aliv:
                    Soldier1.shoot=True
                if (event.key==pygame.K_LSHIFT) or (event.key==pygame.K_RSHIFT) and Soldier1.aliv:
                    Soldier1.throw_grenade=True

            if event.type==pygame.KEYUP:
                if event.key==pygame.K_LEFT:
                    Soldier1.moving_left=False
                if event.key==pygame.K_RIGHT:
                    Soldier1.moving_right=False
                if event.key==pygame.K_UP and Soldier1.aliv:
                    Soldier1.jump=False
                if event.key==pygame.K_SPACE and Soldier1.aliv:
                    Soldier1.shoot=False
                if (event.key==pygame.K_LSHIFT) or (event.key==pygame.K_RSHIFT) and Soldier1.aliv:
                    Soldier1.throw_grenade=False
                    Soldier1.grenade_thrown=False
                    
        pygame.display.update() 
        clock.tick(fps) 

def homescreen():
    exit_homescreen=False
    show_control_menu=False
    while exit_homescreen==False:
        display.blit(homescreen_img,(0,0))
        display.blit(title_img,(screen_width*0.45,screen_height*0.03))
        if start_button.draw():
            click_sound.play()
            gameloop()
            break
        if exit_button.draw():
            exit_homescreen=True
        if controls_button.draw():
            click_sound.play()
            show_control_menu= not(show_control_menu)
        
        if show_control_menu:
            display.blit(controls_menu_img,(0,screen_height*0.2))

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_homescreen=True

        pygame.display.update()
        clock.tick(fps)  
            
homescreen()