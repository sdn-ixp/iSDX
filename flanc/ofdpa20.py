#  Author:
#  Rick Porter (Applied Communication Sciences)

class OFDPA20():
    __shared_state = {}

    def __init__(self, config, origin):
        self.__dict__ = self.__shared_state # makes this a singleton

        self.config = config
        self.origin = origin

    def get_table_id(self):
        print "FDP get_table"
        return 60

    def make_instructions_and_group_mods(self, fm):
        print "FDP make_iagm"
        return ([], [])
