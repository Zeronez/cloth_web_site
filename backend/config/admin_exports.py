import csv

from django.http import HttpResponse


def safe_csv_value(value):
    if value is None:
        return ""
    value = str(value)
    if value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def export_as_csv(*, filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows([[safe_csv_value(value) for value in row] for row in rows])
    return response
