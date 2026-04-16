import time

class ProfileTimer:
    def __init__(self):
        self.init_time_secs = 0
        self.total_time_secs = 0

    def begin_append(self):
        self.init_time_secs = time.time()
    
    def end_append(self):
        self.total_time_secs += time.time() - self.init_time_secs

    def get_total_seconds(self) -> float:
        return self.total_time_secs
