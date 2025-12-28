from typing import Dict
import pygame
from game.app import App
from game.img import *

IMAGE_PATH = Path("uploads")

CORNERSMODELS: Dict[int, List[Tuple[int, int]]] = {
    0: [
        [200, 200],      # top-left
        [600, 200],      # top-right  
        [600, 700],      # bottom-right
        [200, 700]       # bottom-left
    ],
    1: [
        [200, 200],      # top-left
        [1000, 200],      # top-right  
        [1000, 700],      # bottom-right
        [200, 700]       # bottom-left
    ]
}

class Game(App):
    
    def __init__(self):
        super().__init__()
        
        self.corners_model: int = 0
        self.corners: Corners = CORNERSMODELS[self.corners_model]
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
        self.new_image_uploaded = False  # Flag voor nieuwe uploads
        
        # Controller button mapping - detecteer automatisch platform
        self.setup_controller_mapping()
        
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller gevonden: {self.joystick.get_name()}")
            print(f"Aantal buttons: {self.joystick.get_numbuttons()}")
            print(f"Aantal axes: {self.joystick.get_numaxes()}")
    
    def setup_controller_mapping(self):
        """Setup controller button mapping gebaseerd op platform"""
        import platform
        system = platform.system()
        
        # Default mapping (Windows/algemeen)
        self.BTN_NEXT_CORNER = 0
        self.BTN_ZOOM_OUT = 9
        self.BTN_ZOOM_IN = 10
        self.BTN_SAVE = 2
        self.BTN_PLUS = 6
        self.USE_DPAD_AXES = False
        self.USE_DPAD_HAT = False
        
        self.BTN_UP = 11
        self.BTN_RIGHT = 14
        self.BTN_DOWN = 12
        self.BTN_LEFT = 13
        
        # Raspberry Pi / Linux heeft vaak andere mapping
        if system == "Linux":
            # Typische Linux controller mapping
            self.BTN_NEXT_CORNER = 1      # A button
            self.BTN_ZOOM_OUT = 6         # L1
            self.BTN_ZOOM_IN = 5          # R1
            self.BTN_SAVE = 2             # B button
            # D-pad op Linux kan axes OF hat zijn
            self.USE_DPAD_HAT = True  # Nintendo Pro Controller gebruikt hat
            self.DPAD_HAT = 0
        
        print(f"Controller mapping voor {system}:")
        print(f"  Next corner: Button {self.BTN_NEXT_CORNER}")
        print(f"  Zoom: Buttons {self.BTN_ZOOM_OUT}/{self.BTN_ZOOM_IN}")
        print(f"  Save: Button {self.BTN_SAVE}")
        if self.USE_DPAD_HAT:
            print(f"  Pan: Hat {self.DPAD_HAT} (D-pad)")
        elif self.USE_DPAD_AXES:
            print(f"  Pan: Axes (D-pad)")
        else:
            print(f"  Pan: Buttons (D-pad)")
    
    def update(self):
        """Update functie die elke frame wordt aangeroepen"""
        # Check of er een nieuwe foto is geupload
        if self.new_image_uploaded:
            self.new_image_uploaded = False
            self.config_new_img()
        pygame.display.set_caption(str(self.clock.get_fps()))
    
    def config_new_img(self):
        """Wordt aangeroepen vanuit Flask wanneer nieuwe foto is geupload"""
        self.current_corner = 0
        self.corners_model = 0
        self.corners = CORNERSMODELS[self.corners_model]
        self.update_img()
        self.edit_mode = True
        self.zoom = 1
        self.pan_x = 0
        self.pan_y = 0
    
    def next_corners_model(self):
        self.corners_model = (self.corners_model + 1) % len(CORNERSMODELS)
        self.corners = CORNERSMODELS[self.corners_model]
        self.update_img()
    
    def update_img(self):
        """Update de afbeelding met huidige transformaties"""
        self.img = full_pipeline(
            IMAGE_PATH/"current_beamer_image.jpg", 
            self.corners, 
            self.screen.get_size(), 
            self.zoom, 
            self.pan_x, 
            self.pan_y
        )
        self.img = pygame.surfarray.make_surface(np.transpose(self.img, (1, 0, 2)))

    def handle_event(self, event):
        """Handle pygame events"""
        
        # Alleen debug print voor interessante events
        if event.type in [pygame.JOYBUTTONDOWN, pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED]:
            print(f"Event: {event}")
        
        if event.type == pygame.JOYDEVICEADDED:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller verbonden: {self.joystick.get_name()}")
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joystick = None
            print("Controller verwijderd")
            
        if not self.edit_mode:
            return
        
        if event.type == pygame.JOYBUTTONDOWN:
                        
            if self.joystick:
                button = event.button
                # print(f"Button {button} ingedrukt")
                
                # Next corner
                if button == self.BTN_NEXT_CORNER:
                    self.current_corner = self.current_corner + 1
                    if self.current_corner >= len(self.corners):
                        self.current_corner = -1
                        self.update_img()
                    print(f"Corner geselecteerd: {self.current_corner}")
                
                # Zoom
                elif button == self.BTN_ZOOM_OUT:
                    self.zoom -= 0.1
                    self.zoom = max(1, self.zoom)
                    self.update_img()
                    print(f"Zoom: {self.zoom:.2f}")
                elif button == self.BTN_ZOOM_IN:
                    self.zoom += 0.1
                    self.update_img()
                    print(f"Zoom: {self.zoom:.2f}")
                
                elif button == self.BTN_PLUS:
                    self.next_corners_model()
                
                # Save
                elif button == self.BTN_SAVE:
                    print("Opslaan...")
                    save_image(
                        full_pipeline(
                            IMAGE_PATH/"current_beamer_image.jpg", 
                            self.corners, 
                            self.screen.get_size(), 
                            self.zoom, 
                            self.pan_x, 
                            self.pan_y
                        ), 
                        IMAGE_PATH/"mod_image.jpg"
                    )
                    self.edit_mode = False
                    print("Opgeslagen! Edit mode uit.")
            if not self.USE_DPAD_HAT:
                # print(f"Button {event.button} ingedrukt")
                if event.button == self.BTN_UP:
                    self.pan_y -= 10
                elif event.button == self.BTN_DOWN:
                    self.pan_y += 10
                elif event.button == self.BTN_LEFT:
                    self.pan_x -= 10
                elif event.button == self.BTN_RIGHT:
                    self.pan_x += 10
                else:
                    return
                self.update_img()
        
        elif event.type == pygame.JOYAXISMOTION:
            if self.joystick and self.current_corner >= 0:
                # Joystick beweging voor corner positioning
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
        
        # Handle D-pad als hat (Nintendo Pro Controller op Linux)
        elif event.type == pygame.JOYHATMOTION:
            if self.USE_DPAD_HAT and self.edit_mode and event.hat == self.DPAD_HAT:
                x, y = event.value
                if x != 0:
                    self.pan_x += x * 20
                    self.update_img()
                    print(f"Pan X: {self.pan_x}")
                if y != 0:
                    self.pan_y -= y * 20  # Y is omgekeerd in pygame hats
                    self.update_img()
                    print(f"Pan Y: {self.pan_y}")
            
    
    def draw(self):
        """Teken het scherm"""
        # self.screen.fill((255, 255, 255))
        if self.img is not None:
            self.screen.blit(self.img, (0, 0))
            
        if not self.edit_mode:
            return
        
        # Teken polygon
        pygame.draw.polygon(self.screen, (255, 0, 0), self.corners, 5 if self.current_corner < 0 else 0)
        
        # Teken corners
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