import pygame
import sys

class App:
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Pygame Basic App")
        self.clock = pygame.time.Clock()
        self.done = False
        self.fps = 60

    def update(self):
        pass
                
    def draw(self):
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        
    def run(self):
        while not self.done:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
            
            self.update()
            self.draw()
            self.clock.tick(self.fps)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    
    import os
    os.environ['DISPLAY'] = ':0'
    
    app = App()
    app.run()