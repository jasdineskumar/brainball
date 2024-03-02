import pygame
import numpy as np
from pylsl import StreamInlet, resolve_byprop
import utils


class Band:
    Delta = 0
    Theta = 1
    Alpha = 2
    Beta = 3


""" EXPERIMENTAL PARAMETERS """
# Modify these to change aspects of the signal processing

# Length of the EEG data buffer (in seconds)
# This buffer will hold last n seconds of data and be used for calculations
BUFFER_LENGTH = 5

# Length of the epochs used to compute the FFT (in seconds)
EPOCH_LENGTH = 1

# Amount of overlap between two consecutive epochs (in seconds)
OVERLAP_LENGTH = 0.95

# Amount to 'shift' the start of each next consecutive epoch
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH

# Index of the channel(s) (electrodes) to be used
# 0 = left ear, 1 = left forehead, 2 = right forehead, 3 = right ear

INDEX_CHANNEL = [0]
streams = resolve_byprop('type', 'EEG', timeout=2)
if len(streams) == 0:
    raise RuntimeError('Can\'t find EEG stream.')

# Set active EEG stream to inlet and apply time correction
inlet = StreamInlet(streams[0], max_chunklen=12)
eeg_time_correction = inlet.time_correction()

# Get the stream info and description
info = inlet.info()
description = info.desc()

# Get the sampling frequency
# This is an important value that represents how many EEG data points are
# collected in a second. This influences our frequency band calculation.
# for the Muse 2016, this should always be 256
fs = int(info.nominal_srate())

pygame.mixer.init()

# Load and set the volume of the background music
background_music = pygame.mixer.Sound("calm.mp3")
background_music.set_volume(0.6)

# Play the background music in an infinite loop
background_music.play(-1)
class Ball:

    def __init__(self, screen, inlet):
        self.screen = screen
        self.position = [50, 700]
        self.velocity = 0
        self.gravity = 1
        self.inlet = inlet
        self.jumping = False  # Flag to track if the ball is currently jumping
        self.jump_start_position = 0  # Initial position when jump starts
        self.jump_height = 100  # Adjust this value to control jump height
        self.score = 0  # Score attribute to keep track of the player's score

    def calculate_beta_metric(self):
        # Initialize raw EEG data buffer
        eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), 1))
        filter_state = None

        # Compute the number of epochs in "buffer_length"
        n_win_test = int(np.floor((BUFFER_LENGTH - EPOCH_LENGTH) /
                                  SHIFT_LENGTH + 1))

        # Initialize the band power buffer
        band_buffer = np.zeros((n_win_test, 4))

        # Obtain EEG data from the LSL stream
        eeg_data, timestamp = self.inlet.pull_chunk(
            timeout=1, max_samples=int(SHIFT_LENGTH * fs))

        # Only keep the channel we're interested in
        ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]

        # Update EEG buffer with the new data
        eeg_buffer, filter_state = utils.update_buffer(
            eeg_buffer, ch_data, notch=True,
            filter_state=filter_state)

        # Get newest samples from the buffer
        data_epoch = utils.get_last_data(eeg_buffer, EPOCH_LENGTH * fs)

        # Compute band powers
        band_powers = utils.compute_band_powers(data_epoch, fs)
        band_buffer, _ = utils.update_buffer(band_buffer,
                                             np.asarray([band_powers]))

        # Compute the average band powers for all epochs in the buffer
        smooth_band_powers = np.mean(band_buffer, axis=0)

        # Beta Protocol
        beta_metric = smooth_band_powers[Band.Beta] / smooth_band_powers[Band.Theta]
        print("Beta_metric:", beta_metric)

        return beta_metric

    def jump(self):
        if not self.jumping:
            self.jump_start_position = self.position[1]
            self.jumping = True
            self.velocity =-15
            self.horizontal_velocity = 4 # Adjust this value to control horizontal movement during jump
            print("jump")



    def update(self):
        # Check for beta wave threshold
        beta_metric = self.calculate_beta_metric()



        # Jump if the beta wave threshold is met
        if beta_metric >3:
            self.jump()


        if self.jumping:
            self.position[0] += self.horizontal_velocity  # Move horizontally during the jump
            self.velocity += self.gravity
            self.position[1] += self.velocity



            # Check if the ball has reached the jump start position
            if self.position[1] >= self.jump_start_position:
                self.position[1] = self.jump_start_position
                self.velocity = 0
                self.jumping = False

        # Keep the ball above the ground
        if self.position[1] > 700:
            self.position[1] = 700
            self.velocity = 0
            self.jumping = False
        if self.position[0] > 1000:
            self.position[0] = 50  # Reset position to the starting point
            self.position[1] = 700  # Reset position to the starting point




    def get_position(self):
            return tuple(map(int, self.position))

    def get_bottom(self):
            return self.position[1]

    def draw(self):
            pygame.draw.circle(self.screen, pygame.Color('yellow'), self.get_position(), 20)

    def get_score(self):
        return self.score


class Game:
    pygame.mixer.init()
    def __init__(self, surface):
        self.screen = surface
        self.original_background = pygame.image.load("sunset2.jpg").convert()
        self.original_background = pygame.transform.scale(self.original_background, (1000, 800))
        self.background = self.original_background
        self.game_clock = pygame.time.Clock()
        self.FPS = 60
        self.gameRunning = True
        self.close_clicked = False
        self.score = 0
        self.threshold_counter = 0
        self.threshold_seconds = 3
        self.start_time = pygame.time.get_ticks()



        self.ball = Ball(self.screen, inlet)

    def handle_events(self):
        events = pygame.event.get()
        # end the game is player click "close" button
        for event in events:
            # once click close, self.close_clicked =true
            if event.type == pygame.QUIT:
                self.close_clicked = True





    def play(self):
        font = pygame.font.SysFont('', 30, bold=True)  # Font for displaying the score

        title_image = pygame.image.load("brainball.png").convert_alpha()
        title_rect = title_image.get_rect(center=(500, 200))  # Adjust the position of the title

        while (not self.close_clicked) and self.ball.get_bottom() < 790:
            self.handle_events()
            self.screen.fill('black')
            self.screen.blit(self.background, (0, 0))

            # Draw the title image
            self.screen.blit(title_image, title_rect)

            pygame.draw.circle(self.screen, pygame.Color('yellow'), self.ball.get_position(), 20)

            # Display the score
            score_text = font.render("Score: {}".format(self.score), True, pygame.Color('white'))
            self.screen.blit(score_text, (10,10))


            # Check for beta wave threshold
            beta_metric = self.ball.calculate_beta_metric()
            if beta_metric >3:
                self.threshold_counter += 1
                self.score += 1
            else:
                self.threshold_counter = 0
            if self.threshold_counter >= int(self.threshold_seconds / 0.1):
                self.ball.jump()
                self.threshold_counter = 0





            self.ball.update()
            pygame.display.flip()
            self.game_clock.tick(self.FPS)


        if self.ball.get_bottom() >= 790:
            self.afterWin()



    def afterWin(self):
        while not self.close_clicked:
            self.handle_events()
            self.ball.draw()
            self.screen.blit(
                pygame.font.SysFont('', 60, bold=True).render(str("You Win!!"), True, pygame.Color('white')), (50, 50))
            pygame.display.flip()
            self.game_clock.tick(self.FPS)
            if self.close_clicked:
                pygame.quit()


def main():
    pygame.init()
    size = (1000, 800)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("BallGame")
    game = Game(screen)
    game.play()
    pygame.quit()


main()
