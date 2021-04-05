import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import seaborn as sbn
import numpy as np
import zipfile, requests, io, os
import matplotlib.ticker as tick

DATA_URL = 'https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv'

TITLE = {
    1: 'Total Population Over Time',
    2: 'Countries that are the closest by population size',
    3: 'Countries that are the closest by population size'
}
SUBTITLE = {
    1: lambda x: 'Top 5 Populated Countries',
    2: lambda x: f'to {x}',
    3: lambda x: f'to {x}'
}


class TotalPopulation:
    def __init__(self, data_name: str, metadata_name: str, num: int):
        """ Init object by reading distilled data.

        :param str data_name: Name of main dataset
        :param str metadata_name: Name of meta dataset
        :param int num: Chosen action
        """
        self.df = self.load_proper_df(data_name, metadata_name)
        self.palette = pd.DataFrame(np.array(sbn.color_palette('rocket_r', self.df.shape[0])), index=self.df.index)
        self.num = num
        self.title = TITLE[num]
        self.subtitle = SUBTITLE[num]

    def get_data(self, data_name: str, meta_data_name: str):
        """ Load or download worldbank dataset.

        :param str data_name: Name of main dataset
        :param str meta_data_name: Name of meta dataset
        :return:(pd.DataFrame, pd.DataFrame)
        """
        if os.path.isfile(f'../data/{data_name}'):
            df = pd.read_csv(f'../data/{data_name}', sep=',', skiprows=4)
            meta_df = pd.read_csv(f'../data/{meta_data_name}')
        else:
            r = requests.get(DATA_URL, stream=True)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            df = pd.read_csv(z.open(data_name), sep=',', skiprows=4)
            meta_df = pd.read_csv(z.open(meta_data_name))
        return df, meta_df
        
    def load_proper_df(self, data_name: str, meta_data_name: str):
        """ Distill loaded dataset.

        :param str data_name: Name of main dataset
        :param str meta_data_name: Name of meta dataset
        :return: pd.DataFrame
        """
        df, meta_df = self.get_data(data_name, meta_data_name)
        df = df.drop(columns=df.columns[df.isna().sum() == df.shape[0]])
        country_codes = meta_df['Country Code'][~meta_df['Region'].isna()]
        df_proper = df[df['Country Code'].isin(country_codes)].reset_index(drop=True).set_index('Country Name')
        return df_proper.drop(columns=df_proper.columns[df_proper.columns.map(lambda x: not x.isnumeric())])
    
    def create_img(self, series: pd.Series, centroid_name: str = None):
        """ Create image based on given data.

        :param pd.Series series: Data to plot.
        :param str centroid_name: Name of selected Country. (Optional)
        """
        fig, ax = plt.subplots()
        fig.suptitle(self.title, fontsize=14, fontweight='bold')
        plt.yticks(rotation=25)
        plt.xticks(rotation=15)
        if self.num != 1:
            pos = series.index.get_loc(centroid_name)
            ax.get_xticklabels()[pos].set_color("red")

        plot = sbn.barplot(x='Country Name', y=series.name, data=series.reset_index(), ax=ax,
                           palette=self.palette.loc[series.index].values)
        plot.grid(axis='y');
        plot.set_title(self.subtitle(centroid_name));
        plot.yaxis.set_label_position("right")
        plot.set_ylim(0, self.no_max)
        plot.yaxis.set_major_formatter(tick.FuncFormatter(lambda x, _: f'{x / 1000000:,.0f}'))

        for rect, label in zip(plot.patches, np.round(series.values / 1000000, 1)):
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, height + 5, label,
                    ha='center', va='bottom')

        plot.set_ylabel('Population Size [mln]', rotation=270, labelpad=25, fontsize=15)
        plot.set_xlabel('Country Name', labelpad=15, fontsize=15)
        plot.text(0.8, 0.9, series.name, size=20, color='black', transform=ax.transAxes)
        plot = plot.figure
        plot.savefig(f'../images/{self.num}/{series.name}.jpg', bbox_inches=Bbox([[0.0, -0.6], plot.get_size_inches()]))
        plt.close()

    def get_cn(self, series: pd.Series, centroid_name: str):
        """ Get the closest countries (with population size) according to the selected country.

        :param pd.Series series: Candidates for the closest countries in terms of numbers.
        :param centroid_name: Name of selected Country.
        :return: pd.Series
        """
        closest_nat = series.sub(series.loc[centroid_name]).abs().nsmallest(5).index
        return series.loc[closest_nat].sort_values(ascending=False)

    def set_range(self, init_max: float):
        """ Set range of y-axis.

        :param float init_max: Raw max y-axis value.
        """
        denom = np.power(10, np.floor(np.log10(init_max)) - 2)
        self.no_max = np.ceil(init_max / denom) * denom

    def create_imgs_top5(self):
        """ Create images, throughout years, of the top five countries."""
        self.set_range(self.df.max().max() * 1.3)
        self.df.apply(lambda x: self.create_img(x.nlargest(5)))

    def create_imgs_cn_random(self):
        """ Create an image on the basis of randomly picked country and year."""
        random_y = np.random.choice(self.df.columns, size=1)
        random_n = np.random.choice(self.df.index, size=1)
        y2n = dict(zip(random_y, random_n))
        self.set_range(self.df.loc[random_n, random_y].max().max() * 1.3)
        self.df[random_y].apply(lambda x: self.create_img(self.get_cn(x, y2n[x.name]),
                                                          centroid_name=y2n[x.name]))
    def create_imgs_cn(self, centroid_name: str):
        """ Create images, throughout years, given country.

        :param str centroid_name: Name of selected Country.
        """
        self.set_range(self.df.loc[centroid_name].max() * 1.3)
        self.df.apply(lambda x: self.create_img(self.get_cn(x, centroid_name), centroid_name))
        
    def create_gif(self, delay: int = 20):
        """ Create gif based on generated images.

        :param int delay: Delay between images in gif.
        """
        command = f'convert -delay {delay} -loop 0 ../images/{self.num}/*.jpg ../images/hw{self.num}.gif'
        os.system(command)
