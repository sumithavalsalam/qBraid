"""QuantumProgramWrapper Class"""

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import UnsupportedProgramError
from qbraid.transpiler.conversions import convert_from_cirq, convert_to_cirq
from qbraid.transpiler.exceptions import CircuitConversionError


class QuantumProgramWrapper:
    """Abstract class for qbraid program wrapper objects.

    Note: The program wrapper object keeps track of abstract parameters and qubits using an
    intermediate representation. Qubits are stored simplhy as integers, and abstract parameters
    are stored as a :class:`qbraid.transpiler.parameter.ParamID` object, which stores an index in
    addition to a name. All other objects are transpiled directly when the
    :meth:`qbraid.transpiler.QuantumProgramtWrapper.transpile` method is called.

    Attributes:
        program (QPROGRAM): the underlying quantum program object that has been wrapped
        qubits (List[int]): list of integers which represent all the qubits in the circuit,
            typically stored sequentially
        params: (Iterable): list of abstract paramaters in the circuit, stored as
            :class:`qbraid.transpiler.parameter.ParamID` objects
        num_qubits (int): number of qubits in the circuit
        depth (int): the depth of the circuit
        package (str): the package with which the underlying circuit was cosntructed

    """

    def __init__(self, program: QPROGRAM):

        self._program = program
        self._qubits = []
        self._num_qubits = 0
        self._num_clbits = 0
        self._depth = 0
        self._params = []
        self._input_param_mapping = {}
        self._package = None

    @property
    def program(self):
        """Return the underlying quantum program that has been wrapped."""
        return self._program

    @property
    def qubits(self):
        """Return the qubits acted upon by the operations in this circuit"""
        return self._qubits

    @property
    def num_qubits(self):
        """Return the number of qubits in the circuit."""
        return self._num_qubits

    @property
    def num_clbits(self):
        """Return the number of classical bits in the circuit."""
        return self._num_clbits

    @property
    def depth(self):
        """Return the circuit depth (i.e., length of critical path)."""
        return self._depth

    @property
    def params(self):
        """Return the circuit parameters. Defaults to None."""
        return self._params

    @property
    def input_param_mapping(self):
        """Return the input parameter mapping. Defaults to None."""
        return self._input_param_mapping

    @property
    def package(self):
        """Return the original package of the wrapped circuit."""
        return self._package

    def transpile(self, conversion_type):
        """Transpile a qbraid quantum program wrapper object to quantum program object of type
         specified by ``conversion_type``.

        Args:
            conversion_type (str): target package

        Returns:
            quantum program object of type specified by ``package``

        Raises:
            UnsupportedProgramError: If the input program is not supported, or
                conversion to circuit of type ``conversion_type`` is not unsupported.
            CircuitConversionError: If the input program could not be converted to a
                program of type ``conversion_type``.

        """
        if conversion_type == self.package:
            return self.program
        if conversion_type in SUPPORTED_PROGRAM_TYPES:
            try:
                cirq_circuit, _ = convert_to_cirq(self.program)
            except Exception as err:
                raise CircuitConversionError(
                    "Quantum program could not be converted to a Cirq circuit. "
                    "This may be because the program contains custom gates or "
                    f"Pragmas (pyQuil). \n\nProvided program has type {type(self.program)} "
                    f"and is:\n\n{self.program}\n\nQuantum program types supported by the "
                    f"qbraid.transpiler are \n{SUPPORTED_PROGRAM_TYPES}."
                ) from err
            try:
                converted_program = convert_from_cirq(cirq_circuit, conversion_type)
            except Exception as err:
                raise CircuitConversionError(
                    f"Circuit could not be converted from a Cirq type to a "
                    f"circuit of type {conversion_type}."
                ) from err
            return converted_program

        raise UnsupportedProgramError(
            f"Conversion to a program of type {conversion_type} is "
            "unsupported. \n\nQuantum program types supported by the "
            f"qbraid.transpiler are \n{SUPPORTED_PROGRAM_TYPES}"
        )
