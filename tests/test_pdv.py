"""Testes do PDV: leitor de codigo de barras e limite de cards."""
from __future__ import annotations

from app.services.sales_service import SalesService
from app.ui.main_window import PdvPage


def _make_pdv(db, user):
    return PdvPage(db, user, SalesService(db))


def _scan(page, code: str) -> None:
    """Simula o leitor: preenche a busca e dispara o Enter (returnPressed)."""
    page.search_edit.setText(code)
    page.search_edit.returnPressed.emit()


def test_sem_atalho_enter_para_finalizar(qapp, db, user):
    """Return/Enter NAO podem ser atalho de finalizar (causa do bug do leitor)."""
    page = _make_pdv(db, user)
    bad = [a for a in page.actions() if a.shortcut().toString() in ("Return", "Enter")]
    assert not bad, "Ainda existe atalho Return/Enter para finalizar venda"


def test_primeiro_bip_adiciona_ao_carrinho(qapp, db, user, product_factory):
    product_factory("7891234567890", "Produto A")
    page = _make_pdv(db, user)
    page.show()

    _scan(page, "7891234567890")
    assert len(page.cart) == 1
    assert page.cart[0]["qty"] == 1
    assert page.search_edit.text() == "", "Busca deveria limpar apos adicionar"


def test_segundo_bip_mesmo_produto_sobe_quantidade(qapp, db, user, product_factory):
    """Regressao do bug: o 2o bip NAO pode finalizar a venda, so sobe a quantidade."""
    product_factory("7891234567890", "Produto A")
    page = _make_pdv(db, user)
    page.show()

    finalize_calls = []
    page.finalize_sale = lambda: finalize_calls.append(1)

    _scan(page, "7891234567890")
    _scan(page, "7891234567890")

    assert len(page.cart) == 1
    assert page.cart[0]["qty"] == 2
    assert not finalize_calls, "O 2o bip finalizou a venda! Bug reproduzido."


def test_bip_produto_diferente_adiciona_novo_item(qapp, db, user, product_factory):
    product_factory("7891234567890", "Produto A")
    product_factory("7890000000001", "Produto B")
    page = _make_pdv(db, user)
    page.show()

    finalize_calls = []
    page.finalize_sale = lambda: finalize_calls.append(1)

    _scan(page, "7891234567890")
    _scan(page, "7890000000001")

    assert len(page.cart) == 2
    assert not finalize_calls


def test_bip_codigo_inexistente_nao_quebra(qapp, db, user):
    page = _make_pdv(db, user)
    page.show()
    finalize_calls = []
    page.finalize_sale = lambda: finalize_calls.append(1)

    _scan(page, "0000000000000")
    assert len(page.cart) == 0
    assert not finalize_calls
    assert page.search_edit.text() == "0000000000000", "Busca deve manter o codigo para o operador ver"


def test_enter_com_busca_vazia_finaliza(qapp, db, user, product_factory):
    """Caminho deliberado de finalizar pelo teclado: Enter com a busca vazia."""
    product_factory("7891234567890", "Produto A")
    page = _make_pdv(db, user)
    page.show()
    _scan(page, "7891234567890")

    finalize_calls = []
    page.finalize_sale = lambda: finalize_calls.append(1)
    page.search_edit.clear()
    page.search_edit.returnPressed.emit()
    assert finalize_calls, "Enter com busca vazia deveria finalizar a venda"


def test_limite_de_15_cards(qapp, db, user, product_factory):
    """PDV renderiza no maximo 15 cards, mesmo com muitos produtos."""
    for i in range(1, 31):
        product_factory(f"789000{i:04d}", f"Produto {i:03d}")
    page = _make_pdv(db, user)
    page.show()

    assert page.products_grid.count() == 15
    assert "15 de 30" in page.products_count.text()


def test_busca_encontra_produto_alem_do_limite(qapp, db, user, product_factory):
    """A busca encontra qualquer produto, mesmo fora dos 15 visiveis."""
    for i in range(1, 31):
        product_factory(f"789000{i:04d}", f"Produto {i:03d}")
    page = _make_pdv(db, user)
    page.show()

    page.search_edit.setText("Produto 030")
    assert page.products_grid.count() == 1


def test_bip_produto_fora_dos_15_visiveis(qapp, db, user, product_factory):
    """Bipar um codigo fora dos 15 visiveis adiciona ao carrinho."""
    for i in range(1, 31):
        product_factory(f"789000{i:04d}", f"Produto {i:03d}")
    page = _make_pdv(db, user)
    page.show()

    _scan(page, "7890000025")
    assert len(page.cart) == 1
    assert page.cart[0]["name"] == "Produto 025"
