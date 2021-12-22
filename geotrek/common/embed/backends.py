from embed_video.backends import VideoBackend, UnknownIdException
import re


class DailymotionBackend(VideoBackend):
    """
    Backend for Dailymotion URLs.
    """
    re_detect = re.compile(
        r'^(http(s)?://)?(www\.)?dailymotion.com/.*', re.I
    )

    re_code = re.compile(
        r'''dailymotion.com/  # match youtube's domains
            (embed/)?
            video/  # match the embed url syntax
            (?P<code>\w{7})  # match and extract
        ''',
        re.I | re.X
    )
    pattern_url = '{protocol}://www.dailymotion.com/embed/video/{code}'
    pattern_thumbnail_url = '{protocol}://dailymotion.com/thumbnail/embed/video/{code}'

    def get_code(self):
        code = super().get_code()
        if not code:
            raise UnknownIdException('Cannot get ID from `{0}`'.format(self._url))

        return code
