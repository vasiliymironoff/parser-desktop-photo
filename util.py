from fake_useragent import UserAgent


def get_headers():
    return {'user-agent': UserAgent().random}
