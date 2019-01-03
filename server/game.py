from random import randint, choice
import json

import settings
from player import Player
from datatypes import Draw

class Game:

    def __init__(self):
        self._last_id = 0
        self._players = {}
        self.running = False
        self.create_world()

    def next_frame(self):
        if not self.running:
            return

        self.spawn_digit()

        for p_id, p in self._players.items():
            if p.alive:
                p.ws.send_str(json.dumps([["render"] + list(self._draw)]))

    # -----------------------------------------------------

    def create_world(self):
        self._draw = None

    def reset_world(self):
        self._draw = None
        self.send_all("reset_world")

    def new_player(self, name, ws):
        self._last_id += 1
        player_id = self._last_id
        self.send_personal(ws, "handshake", name, player_id)

        for p in self._players.values():
            if p.alive:
                self.send_personal(ws, "joined", p._id, p.name, p.score)

        player = Player(player_id, name, ws)
        self._players[player_id] = player
        self.game_clean(player)

        return player

    def join(self, player):
        if player.alive:
            return
        if self.count_alive_players() == settings.MAX_PLAYERS:
            self.send_personal(player.ws, "error", "Maximum players reached")
            return

        player.start()
        self.send_all("joined", player._id, player.name, 0)

        self.running = False

        if self.count_alive_players() < settings.MAX_PLAYERS:
            self.game_wait(player)
        else:
            self.running = True
            for p_id, p in self._players.items():
                if p.alive:
                    self.game_clean(p)

    def stop(self, player):
        if not player.alive:
            return

        player.score = self._draw.char
        self.send_all_multi(["score", player._id, player.score])
        self.game_wait(player)

        player.alive = False

        if not self.count_alive_players():
            self.send_all("world", self._render_text("GAME OVER"))
            self.send_all("gameover", player._id)

    def player_disconnected(self, player):
        player.ws = None
        if player.alive:
            self.game_over(player)

        del self._players[player._id]
        del player

    # -- Text messages ------------------------------------
    def game_clean(self, player):
        world = [" "] * settings.FIELD_SIZE_X
        if self._draw:
            world[self._draw.x] = self._draw.char

        self.send_personal(player.ws, "world", world)

    def game_wait(self, player):
        self.send_personal(player.ws, "world", self._render_text("WAIT A FRIEND"))

    def _render_text(self, text):
        posx = int(settings.FIELD_SIZE_X / 2 - len(text) / 2)
        world = [" "] * settings.FIELD_SIZE_X
        for i in range(0, len(text)):
            world[posx + i] = text[i]
        return world

    # -----------------------------------------------------
    def count_alive_players(self):
        return sum([int(p.alive) for p in self._players.values()])

    def spawn_digit(self):
        x = randint(0, settings.FIELD_SIZE_X - 1)
        char = str(randint(0,9))
        self._draw = Draw(x, char)

    def send_personal(self, ws, *args):
        msg = json.dumps([args])
        ws.send_str(msg)

    def send_all(self, *args):
        self.send_all_multi([args])

    def send_all_multi(self, commands):
        msg = json.dumps(commands)
        for player in self._players.values():
            if player.ws:
                player.ws.send_str(msg)

