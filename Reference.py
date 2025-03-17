class Reference:
    def __init__(self,frames,points,skeleton):
        self.frames = frames
        self.points = points
        self.skeleton = skeleton


class Deadlift(Reference):
    def __init__(self,frames,points,skeleton):
        super().__init__(self,frames,points,skeleton)

class BenchPress(Reference):
    def __init__(self,frames,points,skeleton):
        super().__init__(self,frames,points,skeleton)

class Squat(Reference):
    def __init__(self,frames,points,skeleton):
        super().__init__(self,frames,points,skeleton)