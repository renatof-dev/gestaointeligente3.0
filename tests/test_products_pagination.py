"""Testes da paginacao da listagem de Produtos (11 por pagina)."""
from __future__ import annotations

from app.ui.main_window import ProductsPage


def _make_page(db, user, count: int, product_factory):
    for i in range(1, count + 1):
        product_factory(f"789000{i:04d}", f"Produto {i:03d}")
    page = ProductsPage(db, user)
    page.show()
    return page


def test_primeira_pagina_tem_11_itens(qapp, db, user, product_factory):
    page = _make_page(db, user, 25, product_factory)
    assert page.table.rowCount() == 11
    assert page.page_label.text() == "Página 1 de 3"
    assert page.products_count_label.text() == "25 produtos"
    assert not page.btn_prev_page.isEnabled()
    assert page.btn_next_page.isEnabled()


def test_navegar_para_proxima_pagina(qapp, db, user, product_factory):
    page = _make_page(db, user, 25, product_factory)
    first_page_first = page._product_rows[0]["name"]

    page.btn_next_page.click()
    assert page.table.rowCount() == 11
    assert page.page_label.text() == "Página 2 de 3"
    assert page.btn_prev_page.isEnabled()
    assert page._product_rows[0]["name"] != first_page_first


def test_ultima_pagina_parcial(qapp, db, user, product_factory):
    page = _make_page(db, user, 25, product_factory)
    page._go_to_page(2)  # 25 = 11 + 11 + 3
    assert page.table.rowCount() == 3
    assert page.page_label.text() == "Página 3 de 3"
    assert not page.btn_next_page.isEnabled()


def test_busca_reseta_para_pagina_1(qapp, db, user, product_factory):
    page = _make_page(db, user, 25, product_factory)
    page._go_to_page(1)
    page.search.setText("Produto 02")  # casa Produto 020..025 -> 6 itens
    assert page._current_page == 0
    assert page.table.rowCount() == 6
    assert page.page_label.text() == "Página 1 de 1"


def test_edicao_mapeia_produto_correto_na_pagina(qapp, db, user, product_factory):
    page = _make_page(db, user, 25, product_factory)
    page._go_to_page(1)  # pagina 2 comeca no produto 12
    page.table.setCurrentCell(0, 0)
    row0_id = int(page._product_rows[0]["id"])
    assert row0_id == 12


def test_excluir_ultimo_item_da_pagina_volta_uma(qapp, db, user, product_factory):
    page = _make_page(db, user, 23, product_factory)  # 23 = 11 + 11 + 1
    # Exclui o unico item da pagina 3
    last_id = int(page._product_rows[0]["id"])  # nao importa; vamos direto no banco
    with db.connect() as conn:
        conn.execute("UPDATE products SET active = 0 WHERE id = (SELECT MAX(id) FROM products)")
    page._go_to_page(2)  # pagina 3 ficou vazia -> clamp para 2
    assert page.page_label.text() == "Página 2 de 2"
    assert page.table.rowCount() == 11
