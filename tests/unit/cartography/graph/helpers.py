from typing import List


def remove_leading_whitespace_and_empty_lines(text: str) -> str:
    """
    Helper function for tests.
    On the given text string, remove all leading whitespace on each line and remove blank lines,
    :param text: Text string
    :return: The text string but with no leading whitespace and no blank lines.
    """
    # We call lstrip() twice on the same line. This is inefficient but ok for small unit tests.
    # Please change it if you want to.
    return "\n".join(
        [line.lstrip() for line in text.split("\n") if line.lstrip() != ""],
    )


def clean_query_list(queries: List[str]) -> List[str]:
    """
    Helper function to remove leading whitespace and blank lines for all strings in the input list.
    :param queries: The list of strings to clean
    :return: A list of text strings with no leading whitespace and no blank lines.
    """
    return [remove_leading_whitespace_and_empty_lines(query) for query in queries]
