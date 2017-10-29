# a mock base pdf exporter

class BasePdfExporter(object):
    def __init__(self,data):
        self.data=data

    def render_pdf(self):
        pass

    def render_to_pdf_response(self):
        pass
