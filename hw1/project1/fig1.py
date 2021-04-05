import argparse
import os


def main(url='https://youtu.be/UkhLvJ6RSKc', file_name='top_10_richest'):
    command1 = f'youtube-dl -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio' \
               f' --merge-output-format mp4 -o {file_name} {url}'
    os.system(command1)
    command2 = f'ffmpeg -i {file_name}.mp4 -filter_complex "fps=10,scale=784:-1:flags=lanczos,split [o1] [o2];[o1]' \
               f' palettegen [p]; [o2] fifo [o3];[o3] [p] paletteuse" {file_name}.gif'
    os.system(command2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--url", required=True, type=str, help="url to youtube video")
    parser.add_argument("-n", "--file_name", required=True, type=str, help="name of the gif")
    args = vars(parser.parse_args())

    main(**args)
