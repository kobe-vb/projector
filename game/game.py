import pygame
from app import App
from img import *

IMAGE_PATH = Path("uploads")

class Game(App):
    
    def __init__(self):
        super().__init__()
        
        self.corners: Corners = [
        [200, 150],      # top-left
        [600, 200],     # top-right  
        [700, 700],     # bottom-right
        [250, 750]       # bottom-left
        ]
        self.zoom: float = 1
        self.pan_x: float = 0
        self.pan_y: float = 0
        
        self.edit_mode = False
        self.img: Optional[pygame.surface.Surface] = None
        if (IMAGE_PATH/"mod_image.jpg").exists():
            self.img = pygame.image.load(IMAGE_PATH/"mod_image.jpg")
        else:
            self.update_img()
            self.edit_mode = True
        
        self.current_corner = -1
        
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        
    def config_new_img(self):
        self.current_corner = 0
        self.update_img()
        self.edit_mode = True
    
    def update_img(self):
        self.img = full_pipeline(IMAGE_PATH/"current_beamer_image.jpg", self.corners, self.screen.get_size(), self.zoom, self.pan_x, self.pan_y)
        self.img = pygame.surfarray.make_surface(np.transpose(self.img, (1, 0, 2)))

    def handle_event(self, event):
                
        if event.type == pygame.JOYDEVICEADDED:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joystick = None
            
        if not self.edit_mode:
            return
        
        if event.type == pygame.JOYBUTTONDOWN:
            if self.joystick:
                # print(event)
                if self.joystick.get_button(0):
                    self.current_corner = self.current_corner + 1
                    if self.current_corner >= len(self.corners):
                        self.current_corner = -1
                        self.update_img()
                elif self.joystick.get_button(4):
                    self.zoom -= 0.1
                    self.zoom = max(0.1, self.zoom)
                    self.update_img()
                elif self.joystick.get_button(6):
                    self.zoom += 0.1
                    self.update_img()
                
                elif self.joystick.get_button(13):
                    self.pan_x += 20
                    self.update_img()
                elif self.joystick.get_button(14):
                    self.pan_x -= 20
                    self.update_img()
                elif self.joystick.get_button(11):
                    self.pan_y += 20
                    self.update_img()
                elif self.joystick.get_button(12):
                    self.pan_y -= 20
                    self.update_img()
                
                elif self.joystick.get_button(2):
                    save_image(full_pipeline(IMAGE_PATH/"current_beamer_image.jpg", self.corners, self.screen.get_size(), self.zoom, self.pan_x, self.pan_y), IMAGE_PATH/"mod_image.jpg")
                    self.edit_mode = False
        
        elif event.type == pygame.JOYAXISMOTION:
            if self.joystick and self.current_corner >= 0:
                x_axis = self.joystick.get_axis(0)
                y_axis = self.joystick.get_axis(1)

                deadzone = 0.1
                if abs(x_axis) < deadzone:
                    x_axis = 0
                if abs(y_axis) < deadzone:
                    y_axis = 0

                speed = 5
                self.corners[self.current_corner][0] += int(x_axis * speed)
                self.corners[self.current_corner][1] += int(y_axis * speed)
                # self.update_img()
        
    def draw(self):
        self.screen.fill((255, 255, 255))
        if self.img is not None:
            self.screen.blit(self.img, (0, 0))
            
        if not self.edit_mode:
            return
        pygame.draw.polygon(self.screen, (255, 0, 0), self.corners, 5 if self.current_corner < 0 else 0)
        
        for i, corner in enumerate(self.corners):
            color = (0, 255, 0)
            if i == self.current_corner:
                color = (255, 0, 0)
            elif i > self.current_corner:
                color = (0, 0, 255)
            pygame.draw.circle(self.screen, color, corner, 10)
        
        

if __name__ == "__main__":
    game = Game()
    game.run()