# a mock base class for csv exporter

class BaseCSVFileExporter(object):
    def __init__(self,data):
        self.data = data

    def render_to_csv(self):
        pass

    def render_to_csv_response(self):
        pass