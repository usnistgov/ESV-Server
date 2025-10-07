import json

class ResponseRBG():

    def __init__(self, rbg_id, entr_jwt, cert_supp):
        self.rbg_id = rbg_id
        self.entr_jwt = entr_jwt
        self.cert_supp = cert_supp

    def toJSON(self):
        print(json.dumps(self, default=lambda o: o.__dict__))
        return json.dumps(self, default=lambda o: o.__dict__)