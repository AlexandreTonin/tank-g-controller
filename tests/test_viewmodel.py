"""
Testes automatizados para o ControlViewModel e orquestração de eventos.
"""

from PySide6.QtWidgets import QApplication
import pytest

from tankg.viewmodel.control_viewmodel import ControlViewModel
from tankg.model.pedal_state import PedalState


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_viewmodel_initialization(qapp, tmp_path):
    state_file = tmp_path / "test_state.json"
    vm = ControlViewModel(state_file=state_file)
    assert vm.state is not None
    assert vm.state.preset in [f"{b}{s}" for b in range(1, 10) for s in "ABCD"]


def test_viewmodel_set_params(qapp, tmp_path):
    state_file = tmp_path / "test_state.json"
    vm = ControlViewModel(state_file=state_file)

    # Modifica parâmetros do amp
    vm.set_amp_type(5)
    assert vm.state.type == 5

    vm.set_amp_param("gain", 92)
    assert vm.state.gain == 92

    # Modifica bypass de módulos
    vm.set_module_bypass("dly", True)
    assert vm.state.dly_on == 1

    vm.set_module_bypass("dly", False)
    assert vm.state.dly_on == 0

    # Troca de preset
    vm.switch_preset("4C")
    assert vm.state.preset == "4C"


def test_viewmodel_gate_and_cab(qapp, tmp_path):
    state_file = tmp_path / "test_state.json"
    vm = ControlViewModel(state_file=state_file)

    vm.set_gate(45)
    assert vm.state.gate == 45

    vm.set_cab(7)
    assert vm.state.cab == 7
