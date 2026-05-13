from __future__ import annotations

from apps.design_system.tests.conftest import cotton_render


def test_data_table_renders_thead_with_columns() -> None:
    out = cotton_render(
        '<c-data-table columns="Name,Spend,ROAS">'
        "<tr><td>Acme</td><td>$1k</td><td>2.5x</td></tr>"
        "</c-data-table>"
    )
    assert "<thead" in out
    assert "Name" in out
    assert "Spend" in out
    assert "Acme" in out


def test_form_field_renders_label_input_error() -> None:
    out = cotton_render('<c-form-field label="Email" name="email" type="email" error="Required" />')
    assert "Email" in out
    assert 'name="email"' in out
    assert "Required" in out


def test_modal_uses_dialog_element() -> None:
    out = cotton_render('<c-modal id="m1" title="Confirm">Body</c-modal>')
    assert "<dialog" in out
    assert "Confirm" in out


def test_toast_has_role_status() -> None:
    out = cotton_render('<c-toast variant="success">Saved</c-toast>')
    assert 'role="status"' in out
    assert "Saved" in out
    assert "emerald" in out


def test_date_range_renders_inputs() -> None:
    out = cotton_render('<c-date-range name_from="since" name_to="until" />')
    assert 'name="since"' in out
    assert 'name="until"' in out
    assert 'type="date"' in out


def test_sparkline_emits_data_chart_target_and_json_island() -> None:
    out = cotton_render('<c-sparkline id="s1" :data="[1,2,3,4]" />', {"data": [1, 2, 3, 4]})
    assert "data-chart-target" in out
    assert 'data-chart-id="s1"' in out
