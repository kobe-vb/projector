import pygame
import sys

class App:
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        pygame.display.set_mode((pygame.display.Info().current_w, pygame.display.Info().current_h))
        print(pygame.display.Info().current_w, pygame.display.Info().current_h)
        pygame.display.set_caption("Pygame Basic App")
        self.clock = pygame.time.Clock()
        self.done = False
        self.fps = 60
    
    def handle_event(self, event):
        pass

    def update(self):
        pass
                
    def draw(self):
        self.screen.fill((0, 0, 0))
        
    def run(self):
        while not self.done:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.done = True
                self.handle_event(event)
            
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    
    import os
    os.environ['DISPLAY'] = ':0'
    
    app = App()
    app.run()