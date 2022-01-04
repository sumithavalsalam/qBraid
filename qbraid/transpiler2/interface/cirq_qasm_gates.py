from typing import Optional, Tuple

import numpy as np

import cirq
from cirq import ops, protocols, value
from cirq.ops import raw_types

# from cirq import linalg
# from cirq.circuits.qasm_output import QasmUGate
# from cirq.ops.parity_gates import ZZPowGate


def rzz(theta):
    if theta == 0:
        return ops.IdentityGate(2)
    elif theta == 2 * np.pi:
        return ops.TwoQubitDiagonalGate([np.pi] * 4)
    else:
        return RZZGate(theta)


class U2Gate(raw_types.Gate):
    def __init__(self, phi, lam):
        self._phi = float(phi)
        self._lam = float(lam)

        super(U2Gate, self)

    def _num_qubits_(self) -> int:
        return 1

    def _unitary_(self):
        isqrt2 = 1 / np.sqrt(2)
        phi = self._phi
        lam = self._lam

        return np.array(
            [
                [isqrt2, -np.exp(1j * lam) * isqrt2],
                [np.exp(1j * phi) * isqrt2, np.exp(1j * (phi + lam)) * isqrt2],
            ],
        )

    def _circuit_diagram_info_(self, args):
        cirq_phi = self._phi / np.pi
        cirq_lam = self._lam / np.pi
        return f"U2({cirq_phi}, {cirq_lam})"


class U3Gate(raw_types.Gate):
    def __init__(self, theta, phi, lam):
        self._theta = float(theta)
        self._phi = float(phi)
        self._lam = float(lam)

        super(U3Gate, self)

    def _num_qubits_(self) -> int:
        return 1

    def _unitary_(self):
        cos = np.cos(self._theta / 2)
        sin = np.sin(self._theta / 2)
        phi = self._phi
        lam = self._lam

        return np.array(
            [
                [cos, -np.exp(complex(0, lam)) * sin],
                [
                    np.exp(complex(0, phi)) * sin,
                    np.exp(complex(0, phi + lam)) * cos,
                ],
            ]
        )

    def _circuit_diagram_info_(self, args):
        cirq_theta = self._theta / np.pi
        cirq_phi = self._phi / np.pi
        cirq_lam = self._lam / np.pi
        return f"U3({cirq_theta}, {cirq_phi}, {cirq_lam})"


class RZZGate(raw_types.Gate):
    def __init__(self, theta):
        self._theta = float(theta)

        super(RZZGate, self)

    def _num_qubits_(self) -> int:
        return 2

    def _unitary_(self):
        itheta2 = 1j * float(self._theta) / 2
        return np.array(
            [
                [np.exp(-itheta2), 0, 0, 0],
                [0, np.exp(itheta2), 0, 0],
                [0, 0, np.exp(itheta2), 0],
                [0, 0, 0, np.exp(-itheta2)],
            ],
        )

    def _circuit_diagram_info_(self, args):
        theta_radians = self._theta / np.pi
        rounded_theta = np.array(theta_radians)
        if args.precision is not None:
            rounded_theta = rounded_theta.round(args.precision)
        gate_str = f"RZZ({rounded_theta})"
        return protocols.CircuitDiagramInfo((gate_str, gate_str))


@value.value_equality
class ZPowGate(ops.ZPowGate):
    def _qasm_(
        self, args: "cirq.QasmArgs", qubits: Tuple["cirq.Qid", ...]
    ) -> Optional[str]:
        args.validate_version("2.0")
        if self._global_shift == 0:
            if self._exponent == 0.25:
                return args.format("t {0};\n", qubits[0])
            if self._exponent == -0.25:
                return args.format("tdg {0};\n", qubits[0])
            if self._exponent == 0.5:
                return args.format("s {0};\n", qubits[0])
            if self._exponent == -0.5:
                return args.format("sdg {0};\n", qubits[0])
            if self._exponent == 1:
                return args.format("z {0};\n", qubits[0])
            return args.format(
                "p({0:half_turns}) {1};\n", self._exponent, qubits[0]
            )
        return args.format(
            "rz({0:half_turns}) {1};\n", self._exponent, qubits[0]
        )


# # OLD CODE
# if self._global_shift == -0.5:
#     return args.format(
#         'rz({0:half_turns}) {1};\n', self._exponent, qubits[0]
#     )
# coefficient = 1j ** (2 * self._exponent * self._global_shift)
# matrix = coefficient * np.eye(2)
# cirq_circuit = cirq.Circuit(
#     [
#         cirq.Moment([self.to_su2()(qubits[0])]),
#         cirq.Moment([cirq.MatrixGate(matrix)(qubits[0])]),
#     ]
# )
# print(args)
# qasms = [
#     protocols.qasm(op, args=args) for op in cirq_circuit.all_operations()
# ]
# print(qasms)
# angles = linalg.deconstruct_single_qubit_matrix_into_angles(matrix)
# pre_phase, rotation, post_phase = angles
# return args.format(
#     'rz({0:half_turns}) {1};\nu3({2:half_turns},{3:half_turns},{4:half_turns}) {5};\n',
#     self._exponent,
#     qubits[0],
#     rotation / np.pi,
#     post_phase / np.pi,
#     pre_phase / np.pi,
#     qubits[0],
# )