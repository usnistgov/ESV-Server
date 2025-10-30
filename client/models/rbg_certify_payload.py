class Rbg_Certify_Payload:

    def __init__(self, entropy_id, rbg, supporting_documentation, module_id=0, vendor_id=0):
        self.entropy_id = entropy_id
        self.module_id = module_id
        self.vendor_id = vendor_id
        self.rbg = rbg
        self.supporting_documentation = supporting_documentation

