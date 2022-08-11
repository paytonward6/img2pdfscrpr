import pytest

from img2pdfscrpr.img2pdfscrpr import ImageDownloader

temp = ImageDownloader()

def test_get_url():
    assert temp.parse_url('https://trufflewufflepigs.com/PidAndCorn.jpeg/') =='https://trufflewufflepigs.com/PidAndCorn.jpeg/'
