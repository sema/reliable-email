
class WorkerRemoteError(Exception):
    def __init__(self, *args, **kwargs):
        super(WorkerRemoteError, self).__init__(*args, **kwargs)


class WorkerInvalidEmail(Exception):
    def __init__(self, *args, **kwargs):
        super(WorkerInvalidEmail, self).__init__(*args, **kwargs)


class WorkerTemporaryError(Exception):
    def __init__(self, *args, **kwargs):
        super(WorkerTemporaryError, self).__init__(*args, **kwargs)
