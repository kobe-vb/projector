from app import App
from img import *

class Game(App):
    
    def __init__(self):
        super().__init__()
        self.img = full_pipeline()
    