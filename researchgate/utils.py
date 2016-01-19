from pip._vendor.progress.bar import ShadyBar


class ProgressBar(ShadyBar):
    message = "%(description)s"
    suffix = "%(percent).1f%% eta %(eta)s s"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = ''
