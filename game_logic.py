"""Spel logica - normale Python classes voor het spel"""
import random


class Hand:
    """De hand van de speler"""
    def __init__(self, bet):
        self.bet = bet          # Inzet in euro's
        self.rolls = []         # Lijst van gedobbelde waarden
        self.cut_used = False   # Of 'Cut the fuse' al is gebruikt
        self.result = None      # Uitslag: Win, Lose, Bust, etc.
        self.active = True      # Of de hand nog actief is

    @property
    def total(self):
        """Totale waarde van de hand"""
        return sum(self.rolls)

    def roll(self):
        """Rol een d12 en voeg toe aan de hand"""
        self.rolls.append(random.randint(1, 12))
        return self.rolls[-1]

    def check_bust(self):
        """Check of de hand bust is (> 24)"""
        if self.total > 24:
            self.result = 'Bust'
            self.active = False
            return True
        return False

    def check_six_dice_win(self):
        """Check of speler 6 dobbelstenen heeft zonder bust"""
        if len(self.rolls) >= 6 and self.total <= 24:
            self.result = 'Win (6 dice)'
            self.active = False
            return True
        return False


class Game:
    """De status van het hele spel"""
    def __init__(self, bet):
        self.hand = Hand(bet)   # Hand van de speler
        self.scar_rolls = []    # Dobbelstenen van de Scar (dealer)
        self.round = 1          # Huidige ronde (1, 2, of 3)
        self.game_over = False  # Of het spel afgelopen is

    @property
    def scar_total(self):
        """Totale waarde van de Scar"""
        return sum(self.scar_rolls)

    def scar_roll(self):
        """Scar rolt tot 18, 24, of bust"""
        while self.scar_total < 18 and self.scar_total != 24:
            self.scar_rolls.append(random.randint(1, 12))
            if self.scar_total > 24:
                break

    def check_scar_whitejack(self):
        """Check of Scar 24 heeft op eerste worp"""
        if self.scar_total == 24:
            self.game_over = True
            self.hand.result = 'Lose (Scar Whitejack)'
            return True
        return False

    def determine_winner(self):
        """Bepaal de winnaar aan het einde van het spel"""
        if self.hand.result:
            return

        scar = self.scar_total
        player = self.hand.total

        if scar > 24:
            self.hand.result = 'Win (Scar bust)'
        elif player > scar:
            self.hand.result = 'Win'
        elif player < scar:
            self.hand.result = 'Lose'
        else:
            self.hand.result = 'Push'

        self.hand.active = False
        self.game_over = True
