from rest_framework.response import Response
from rest_framework import status

from export.pdf import BasePdfExporter
from export.csvfile import BaseCSVFileExporter


class ScheduleCalendarExporter(BasePdfExporter):
    def render_to_pdf_response(self):
        return Response(data={'url':"/static/export/calendar.pdf"},status=status.HTTP_200_OK)

class EmployeeSlotTableExporter(BaseCSVFileExporter):
    def render_to_csv_response(self):
        return Response(data={'url':"/static/export/employee-slot.csv"},status=status.HTTP_200_OK)

class TimeClockTableExporter(BaseCSVFileExporter):
    def render_to_csv_response(self):
        return Response(data={'url':"/static/export/time-clock.csv"},status=status.HTTP_200_OK)

class ScheduleSlotTableExporter(BaseCSVFileExporter):
    def render_to_csv_response(self):
        return Response(data={'url':"/static/export/schedule-slot.csv"},status=status.HTTP_200_OK)