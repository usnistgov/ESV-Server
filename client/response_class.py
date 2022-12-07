import json

class Response():

    def __init__(self, ea_id, df_ids, entr_jwt, cert_supp):
        self.ea_id = ea_id
        self.df_ids = df_ids
        self.entr_jwt = entr_jwt
        self.cert_supp = cert_supp

    def toJSON(self):
        print(json.dumps(self, default=lambda o: o.__dict__))
        return json.dumps(self, default=lambda o: o.__dict__)