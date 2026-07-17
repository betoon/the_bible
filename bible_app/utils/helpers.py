"""General helper functions."""


def markdown_line(value):
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n")

