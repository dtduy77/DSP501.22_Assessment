
import os
from detect.detect_song import detect_song

file_can_test = "data/music_noisy_2.wav" 



def main():
    
    current_dir = os.getcwd()
    full_path = os.path.join(current_dir, file_can_test)

    detect_song(full_path)

if __name__ == "__main__":
    main()