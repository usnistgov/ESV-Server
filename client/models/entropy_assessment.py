class Entropy_Assessment:

    def __init__(self, ea_id, oe_id=0, raw_noise_id=0, restart_id=0, conditioned=None, access_token=""):
        self.ea_id = int(ea_id)
        self.raw_noise_id = int(raw_noise_id)
        self.restart_id = int(restart_id)
        self.conditioned = conditioned
        self.access_token = access_token
        self.oe_id = int(oe_id)

class Conditioned_File:

    def __init__(self, id, sequence_position):
        self.id = int(id)
        self.sequence_position = int(sequence_position)