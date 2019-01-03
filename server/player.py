class Player:
    def __init__(self, player_id, name, ws):
        self._id = player_id
        self.name = name
        self.ws = ws
        self.alive = False
        self.score = 0

    def start(self):
        self.alive = True
