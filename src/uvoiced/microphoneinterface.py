class MicrophoneInterface:


    @property    
    def is_above_background(self):
        raise NotImplementedError()
    
    def read_pcm16(self, record_mode=True):
        raise NotImplementedError()
    
    def close(self):
        raise NotImplementedError()
    

