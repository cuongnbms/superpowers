from src.pagination import paginate, total_pages


def test_empty_list_has_one_page():
    assert total_pages(0, 10) == 1


def test_total_pages_rounds_up():
    assert total_pages(25, 10) == 3


def test_paginate_empty_list():
    assert paginate([], 1, 10) == []
