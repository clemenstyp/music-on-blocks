
from time import time
from MusicLogging import MusicLogging

class NFC_DEMO:
    lastTime = 0
    tags= ["aaaaaaaa", "", "bbbbb","",  "ccccccc", ""]
    currentTag = 0
    def read(self):
        self.currentTime = time()

        if int(self.currentTime/60) is self.lastTime:
            self.lastTime = int(self.currentTime/60)
            self.currentTag = self.currentTag +1
            if self.currentTag > len(self.tags):
                self.currentTag = 0
        return self.tags[self.currentTag]

    def stop(self):
        MusicLogging.Instance().info("stopping reader")


