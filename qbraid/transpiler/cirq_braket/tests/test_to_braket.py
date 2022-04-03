"""
Unit tests for converting Cirq circuits to Braket circuits
"""

import numpy as np
import pytest
from cirq import Circuit, LineQubit, ops, testing

from qbraid.interface import equal_unitaries, to_unitary
from qbraid.transpiler.cirq_braket.convert_to_braket import to_braket


@pytest.mark.parametrize("qreg", (LineQubit.range(2), [LineQubit(1), LineQubit(6)]))
def test_to_braket_bell_circuit(qreg):
    """Test converting bell circuit"""
    cirq_circuit = Circuit(ops.H(qreg[0]), ops.CNOT(*qreg))
    braket_circuit = to_braket(cirq_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


def test_to_braket_non_parameterized_single_qubit_gates():
    """Test converting circuit containing non-parameterized single-qubits gates"""
    qreg = LineQubit.range(4)
    cirq_circuit = Circuit(
        ops.I(qreg[0]),
        ops.X(qreg[1]),
        ops.Y(qreg[2]),
        ops.Z(qreg[3]),
        ops.H(qreg[0]),
        ops.S(qreg[1]),
        ops.S(qreg[2]) ** -1,
        ops.T(qreg[3]),
        ops.T(qreg[0]) ** -1,
        ops.X(qreg[1]) ** 0.5,
        ops.X(qreg[2]) ** -0.5,
    )
    braket_circuit = to_braket(cirq_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


@pytest.mark.parametrize("qubit_index", (0, 3))
def test_to_braket_parameterized_single_qubit_gates(qubit_index):
    """Testing converting circuit containing parameterized single-qubit gates"""
    qubit = LineQubit(qubit_index)
    angles = np.random.RandomState(11).random(4)  # pylint: disable=no-member
    cirq_circuit = Circuit(
        ops.rx(angles[0]).on(qubit),
        ops.ry(angles[1]).on(qubit),
        ops.rz(angles[2]).on(qubit),
        ops.Z.on(qubit) ** (angles[3] / np.pi),
    )
    braket_circuit = to_braket(cirq_circuit)
    print(braket_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


def test_to_braket_non_parameterized_two_qubit_gates():
    """Test converting circuit containing non-parameterized two-qubit gates."""
    qreg = LineQubit.range(2, 5)
    cirq_circuit = Circuit(
        ops.CNOT(*qreg[:2]),
        ops.SWAP(*qreg[1:]),
        ops.ISWAP(*qreg[:2]),
        ops.CZ(*qreg[1:]),
        ops.ControlledGate(ops.Y).on(*qreg[:2]),
    )
    braket_circuit = to_braket(cirq_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


def test_to_braket_three_qubit_gates():
    """Testing converting circuits containing three-qubit gates"""
    qreg = LineQubit.range(1, 4)
    cirq_circuit = Circuit(ops.TOFFOLI(*qreg), ops.FREDKIN(*qreg))
    braket_circuit = to_braket(cirq_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


def _rotation_of_pi_over_7(num_qubits):
    matrix = np.identity(2**num_qubits)
    matrix[0:2, 0:2] = [
        [np.cos(np.pi / 7), np.sin(np.pi / 7)],
        [-np.sin(np.pi / 7), np.cos(np.pi / 7)],
    ]
    return matrix


@pytest.mark.skip(reason="Unsupported gates become unitaries.")
def test_to_braket_raises_on_unsupported_gates():
    """Test that converting circuit with unsupported gate raises error"""
    for num_qubits in range(3, 5):
        print(num_qubits)
        qubits = [LineQubit(int(qubit)) for qubit in range(num_qubits)]
        op = ops.MatrixGate(_rotation_of_pi_over_7(num_qubits)).on(*qubits)
        circuit = Circuit(op)
        with pytest.raises(ValueError):
            to_braket(circuit)


def test_to_braket_common_one_qubit_gates():
    """These gates should stay the same (i.e., not get decomposed) when
    converting Cirq -> Braket.
    """
    rots = [ops.rx, ops.ry, ops.rz]
    angles = [1 / 5, 3 / 5, -4 / 5]
    qubit = LineQubit(0)
    cirq_circuit = Circuit(
        # Paulis.
        ops.X(qubit),
        ops.Y(qubit),
        ops.Z(qubit),
        # Single-qubit rotations.
        [rot(angle).on(qubit) for rot, angle in zip(rots, angles)],
        # Rz alter egos.
        ops.T(qubit),
        ops.T(qubit) ** -1,
        ops.S(qubit),
        ops.S(qubit) ** -1,
        # Rx alter egos.
        ops.X(qubit) ** 0.5,
        ops.X(qubit) ** -0.5,
    )

    braket_circuit = to_braket(cirq_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


@pytest.mark.parametrize("uncommon_gate", [ops.HPowGate(exponent=-1 / 14)])
def test_to_braket_uncommon_one_qubit_gates(uncommon_gate):
    """These gates get decomposed when converting Cirq -> Braket, but
    the unitaries should be equal up to global phase.
    """
    cirq_circuit = Circuit(uncommon_gate.on(LineQubit(0)))
    braket_circuit = to_braket(cirq_circuit)
    cirq_unitary = to_unitary(cirq_circuit)
    braket_unitary = to_unitary(braket_circuit)
    testing.assert_allclose_up_to_global_phase(
        braket_unitary,
        cirq_unitary,
        atol=1e-7,
    )


@pytest.mark.parametrize(
    "common_gate",
    [
        ops.CNOT,
        ops.CZ,
        ops.ISWAP,
        ops.XXPowGate(exponent=-0.2),
        ops.YYPowGate(exponent=0.3),
        ops.ZZPowGate(exponent=-0.1),
    ],
)
def test_to_braket_common_two_qubit_gates(common_gate):
    """These gates should stay the same (i.e., not get decomposed) when
    converting Cirq -> Braket.
    """
    cirq_circuit = Circuit(common_gate.on(*LineQubit.range(2)))
    braket_circuit = to_braket(cirq_circuit)
    if not isinstance(common_gate, (ops.XXPowGate, ops.YYPowGate, ops.ZZPowGate)):
        equal_unitaries(braket_circuit, cirq_circuit)
    else:
        cirq_unitary = to_unitary(cirq_circuit)
        braket_unitary = to_unitary(braket_circuit)
        testing.assert_allclose_up_to_global_phase(
            braket_unitary,
            cirq_unitary,
            atol=1e-7,
        )


@pytest.mark.parametrize(
    "uncommon_gate",
    [ops.CNotPowGate(exponent=-1 / 17), ops.CZPowGate(exponent=2 / 7)],
)
def test_to_braket_uncommon_two_qubit_gates(uncommon_gate):
    """These gates get decomposed when converting Cirq -> Braket, but
    the unitaries should be equal up to global phase.
    """
    cirq_circuit = Circuit(uncommon_gate.on(*LineQubit.range(2)))
    braket_circuit = to_braket(cirq_circuit)
    cirq_unitary = to_unitary(cirq_circuit)
    braket_unitary = to_unitary(braket_circuit)
    testing.assert_allclose_up_to_global_phase(
        braket_unitary,
        cirq_unitary,
        atol=1e-7,
    )


@pytest.mark.parametrize(
    "common_gate",
    [
        ops.TOFFOLI,
        ops.FREDKIN,
    ],
)
def test_to_braket_common_three_qubit_gates(common_gate):
    """These gates should stay the same (i.e., not get decomposed) when
    converting Cirq -> Braket.
    """
    cirq_circuit = Circuit(common_gate.on(*LineQubit.range(3)))
    braket_circuit = to_braket(cirq_circuit)
    assert equal_unitaries(braket_circuit, cirq_circuit)


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_50_random_circuits(num_qubits):
    """Testing converting 50 random circuits"""
    for i in range(10):
        moments = np.random.randint(1, 6)
        state = num_qubits + i
        cirq_circuit = testing.random_circuit(
            num_qubits, n_moments=moments, op_density=1, random_state=state
        )
        braket_circuit = to_braket(cirq_circuit)
        if not equal_unitaries(braket_circuit, cirq_circuit):
            print()
            print(cirq_circuit)
            print()
            print(braket_circuit)
            print()
            assert False
    assert True