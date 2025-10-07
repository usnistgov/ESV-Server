class Certify_Payload:

    def __init__(self, entropy_id, module_id, vendor_id, entropy_assessments, supporting_documentation, entropy_certificate = None):
        self.entropy_id = entropy_id
        self.module_id = module_id
        self.vendor_id = vendor_id
        self.entropy_certificate = entropy_certificate
        self.entropy_assessments = entropy_assessments
        self.supporting_documentation = supporting_documentation

