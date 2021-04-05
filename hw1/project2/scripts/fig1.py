import argparse
from tools import TotalPopulation


def main(data_name, metadata_name):
    tot_pop = TotalPopulation(data_name, metadata_name, num=1)
    tot_pop.create_imgs_top5()
    tot_pop.create_gif()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--data_name", required=False, type=str, help="name of main file")
    parser.add_argument("-n", "--metadata_name", required=False, type=str, help="name of metadata file")
    args = vars(parser.parse_args())

    main(**args)