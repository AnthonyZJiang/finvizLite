from datetime import datetime, date
from .util import (
    web_scrap,
    image_scrap,
    number_covert,
    format_datetime,
)

QUOTE_URL = "https://finviz.com/quote.ashx?t={ticker}"
NUM_COL = [
    "P/E",
    "EPS (ttm)",
    "Insider Own",
    "Shs Outstand",
    "Market Cap",
    "Forward P/E",
    "EPS nest Y",
    "Insider ",
]


class Quote:
    """quote
    Getting current price of the ticker

    """

    def get_current(self, ticker):
        """Getting current price of the ticker.

        Returns:
            price(float): price of the ticker
        """
        soup = web_scrap("https://finviz.com/request_quote.ashx?t={}".format(ticker))
        return soup.text


class FinvizLite:
    """finvizlit
    Getting information from the individual ticker.

    Args:
        ticker(str): ticker string
        verbose(int): choice of visual the progress. 1 for visualize progress.
    """

    def __init__(
        self,
        ticker,
        verbose=0,
    ):
        """initiate module"""

        self.ticker = ticker
        self.flag = False
        self.quote_url = QUOTE_URL.format(ticker=ticker)
        self.soup = web_scrap(self.quote_url)
        if self._checkexist(verbose):
            self.flag = True
        self.info = {}

    def _checkexist(self, verbose):
        try:
            if "not found" in self.soup.find("td", class_="body-text").text:
                print("Ticker not found.")
                return False
        except:
            if verbose == 1:
                print("Ticker exists.")
            return True

    def ticker_charts(
        self, timeframe="daily", charttype="advanced", out_dir="", urlonly=False
    ):
        """Download ticker charts.

        Args:
            timeframe(str): choice of timeframe (daily, weekly, monthly).
            charttype(str): choice of type of chart (candle, line, advanced).
            out_dir(str): output image directory. default none.
            urlonly (bool): choice of downloading charts, default: downloading chart

        Returns:
            charturl(str): url for the chart
        """
        if timeframe not in ["daily", "weekly", "monthly"]:
            raise ValueError("Invalid timeframe '{}'".format(timeframe))
        if charttype not in ["candle", "line", "advanced"]:
            raise ValueError("Invalid chart type '{}'".format(charttype))
        url_type = "c"
        url_ta = "0"
        if charttype == "line":
            url_type = "l"
        elif (
            charttype == "advanced" and timeframe != "weekly" and timeframe != "monthly"
        ):
            url_ta = "1"

        url_timeframe = "d"
        if timeframe == "weekly":
            url_timeframe = "w"
        elif timeframe == "monthly":
            url_timeframe = "m"
        chart_url = "https://finviz.com/chart.ashx?t={ticker}&ty={type}&ta={ta}&p={timeframe}".format(
            ticker=self.ticker, type=url_type, ta=url_ta, timeframe=url_timeframe
        )
        if not urlonly:
            image_scrap(chart_url, self.ticker, out_dir)
        return chart_url

    def ticker_fundament(self, raw=True):
        """Get ticker fundament.

        Args:
            raw(boolean): if True, the data is raw.

        Returns:
            fundament(dict): ticker fundament.
        """
        fundament_info = {}

        fundament_info["Company"] = self.soup.find(
            "h2", class_="quote-header_ticker-wrapper_company"
        ).text.strip()
        quote_links = self.soup.find("div", class_="quote-links")
        links = quote_links.find_all("a")
        fundament_info["Sector"] = links[0].text
        fundament_info["Industry"] = links[1].text
        fundament_info["Country"] = links[2].text
        fundament_info["Exchange"] = links[3].text

        fundament_table = self.soup.find("table", class_="snapshot-table2")
        rows = fundament_table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            cols = [i.text for i in cols]
            fundament_info = self._parse_column(cols, raw, fundament_info)
        self.info["fundament"] = fundament_info

        return fundament_info

    def _parse_column(self, cols, raw, fundament_info):
        header = ""
        for i, value in enumerate(cols):
            if i % 2 == 0:
                header = value
            else:
                if header == "Volatility":
                    fundament_info = self._parse_volatility(
                        header, fundament_info, value, raw
                    )
                elif header == "52W Range":
                    fundament_info = self._parse_52w_range(
                        header, fundament_info, value, raw
                    )
                elif header == "Optionable" or header == "Shortable":
                    if raw:
                        fundament_info[header] = value
                    elif value == "Yes":
                        fundament_info[header] = True
                    else:
                        fundament_info[header] = False
                else:
                    # Handle EPS Next Y keys with two different values
                    if header == "EPS next Y" and header in fundament_info.keys():
                        header += " Percentage"
                    if raw:
                        fundament_info[header] = value
                    else:
                        try:
                            fundament_info[header] = number_covert(value)
                        except ValueError:
                            fundament_info[header] = value
        return fundament_info

    def _parse_52w_range(self, header, fundament_info, value, raw):
        info_header = ["52W Range From", "52W Range To"]
        info_value = [0, 2]
        self._parse_value(header, fundament_info, value, raw, info_header, info_value)
        return fundament_info

    def _parse_volatility(self, header, fundament_info, value, raw):
        info_header = ["Volatility W", "Volatility M"]
        info_value = [0, 1]
        self._parse_value(header, fundament_info, value, raw, info_header, info_value)
        return fundament_info

    def _parse_value(self, header, fundament_info, value, raw, info_header, info_value):
        try:
            value = value.split()
            if raw:
                for i, value_index in enumerate(info_value):
                    fundament_info[info_header[i]] = value[value_index]
            else:
                for i, value_index in enumerate(info_value):
                    fundament_info[info_header[i]] = number_covert(value[value_index])
        except:
            fundament_info[header] = value
        return fundament_info

    def ticker_description(self):
        """Get ticker description.

        Returns:
            description(str): ticker description.
        """
        return self.soup.find("td", class_="fullview-profile").text


    def ticker_outer_ratings(self):
        """Get outer ratings table.

        Returns:
            df(pandas.DataFrame): outer ratings table
        """
        fullview_ratings_outer = self.soup.find("table", class_="js-table-ratings")
        if fullview_ratings_outer is None:
            return None
        ratings = []
        try:
            rows = fullview_ratings_outer.find_all(
                "td", class_="fullview-ratings-inner"
            )
            if len(rows) == 0:
                rows = fullview_ratings_outer.find_all("tr")[1:]
            for row in rows:
                each_row = row.find("tr")
                if not each_row:
                    each_row = row
                cols = each_row.find_all("td")
                rating_date = cols[0].text
                if rating_date.lower().startswith("today"):
                    rating_date = date.today()
                else:
                    rating_date = datetime.strptime(rating_date, "%b-%d-%y")

                status = cols[1].text
                outer = cols[2].text
                rating = cols[3].text
                price = cols[4].text
                info_dict = {
                    "Date": rating_date,
                    "Status": status,
                    "Outer": outer,
                    "Rating": rating,
                    "Price": price,
                }
                ratings.append(info_dict)
            self.info["ratings_outer"] = ratings
            return ratings
        except AttributeError:
            return None

    def ticker_news(self):
        """Get news information table.

        Returns:
            news(dict): news information table
        """
        fullview_news_outer = self.soup.find("table", class_="fullview-news-outer")
        if fullview_news_outer is None:
            return None
        
        rows = fullview_news_outer.find_all("tr")
        
        news = []
        last_date = ""
        for row in rows:
            try:
                cols = row.find_all("td")
                news_date = cols[0].text
                title = cols[1].a.text
                link = cols[1].a["href"]
                source = cols[1].span.text[1:-1]
                news_time = news_date.split()
                if len(news_time) == 2:
                    last_date = news_time[0]
                    news_time = " ".join(news_time)
                else:
                    news_time = last_date + " " + news_time[0]

                news_time = format_datetime(news_time)

                info_dict = {"Date": news_time, "Title": title, "Link": link, "Source": source}
                news.append(info_dict)
            except AttributeError:
                pass
        
        self.info["news"] = news
        return news

    def ticker_full_info(self):
        """Get all the ticker information.

        Returns:
            df(pandas.DataFrame): insider information table
        """
        self.ticker_fundament()
        self.ticker_news()
        return self.info
