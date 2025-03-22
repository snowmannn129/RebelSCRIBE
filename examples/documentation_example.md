# Example Documentation Project

This is an example documentation project for RebelSCRIBE.

## Project Structure

- Title: QuantumLib API Documentation
- Version: 1.0.0
- Author: QuantumTech Inc.

## Overview

QuantumLib is a Python library for quantum computing simulations. It provides a high-level interface for creating and manipulating quantum circuits, as well as tools for simulating quantum algorithms.

## Installation

```bash
pip install quantumlib
```

## Usage

```python
import quantumlib as ql

# Create a quantum circuit with 2 qubits
circuit = ql.QuantumCircuit(2)

# Apply a Hadamard gate to the first qubit
circuit.h(0)

# Apply a CNOT gate with the first qubit as control and the second qubit as target
circuit.cx(0, 1)

# Measure both qubits
circuit.measure_all()

# Simulate the circuit
result = ql.simulate(circuit, shots=1000)

# Print the results
print(result.counts)
```

## API Reference

### QuantumCircuit

The `QuantumCircuit` class represents a quantum circuit.

#### Constructor

```python
QuantumCircuit(num_qubits, num_bits=None)
```

- `num_qubits`: The number of qubits in the circuit.
- `num_bits`: The number of classical bits in the circuit. If not specified, it defaults to the number of qubits.

#### Methods

##### h(qubit)

Apply a Hadamard gate to the specified qubit.

- `qubit`: The index of the qubit to apply the gate to.

##### x(qubit)

Apply a Pauli-X gate to the specified qubit.

- `qubit`: The index of the qubit to apply the gate to.

##### y(qubit)

Apply a Pauli-Y gate to the specified qubit.

- `qubit`: The index of the qubit to apply the gate to.

##### z(qubit)

Apply a Pauli-Z gate to the specified qubit.

- `qubit`: The index of the qubit to apply the gate to.

##### cx(control, target)

Apply a CNOT gate with the specified control and target qubits.

- `control`: The index of the control qubit.
- `target`: The index of the target qubit.

##### measure(qubit, bit=None)

Measure the specified qubit and store the result in the specified classical bit.

- `qubit`: The index of the qubit to measure.
- `bit`: The index of the classical bit to store the result in. If not specified, it defaults to the same index as the qubit.

##### measure_all()

Measure all qubits and store the results in the corresponding classical bits.

### simulate

The `simulate` function simulates a quantum circuit.

```python
simulate(circuit, shots=1024)
```

- `circuit`: The quantum circuit to simulate.
- `shots`: The number of times to run the simulation. Defaults to 1024.

Returns a `SimulationResult` object.

### SimulationResult

The `SimulationResult` class represents the result of a quantum circuit simulation.

#### Attributes

##### counts

A dictionary mapping measurement outcomes to their frequencies.

For example, if the circuit measures two qubits, the keys of the dictionary will be strings like "00", "01", "10", and "11", and the values will be the number of times each outcome occurred in the simulation.

## Examples

### Creating a Bell State

```python
import quantumlib as ql

# Create a quantum circuit with 2 qubits
circuit = ql.QuantumCircuit(2)

# Apply a Hadamard gate to the first qubit
circuit.h(0)

# Apply a CNOT gate with the first qubit as control and the second qubit as target
circuit.cx(0, 1)

# Measure both qubits
circuit.measure_all()

# Simulate the circuit
result = ql.simulate(circuit, shots=1000)

# Print the results
print(result.counts)
```

Expected output:

```
{"00": 500, "11": 500}
```

### Implementing Grover's Algorithm

```python
import quantumlib as ql

# Create a quantum circuit with 2 qubits
circuit = ql.QuantumCircuit(2)

# Apply Hadamard gates to both qubits
circuit.h(0)
circuit.h(1)

# Apply the oracle (in this case, we're searching for the state |11⟩)
circuit.x(0)
circuit.x(1)
circuit.h(1)
circuit.cx(0, 1)
circuit.h(1)
circuit.x(0)
circuit.x(1)

# Apply Hadamard gates to both qubits
circuit.h(0)
circuit.h(1)

# Apply the diffusion operator
circuit.x(0)
circuit.x(1)
circuit.h(1)
circuit.cx(0, 1)
circuit.h(1)
circuit.x(0)
circuit.x(1)

# Apply Hadamard gates to both qubits
circuit.h(0)
circuit.h(1)

# Measure both qubits
circuit.measure_all()

# Simulate the circuit
result = ql.simulate(circuit, shots=1000)

# Print the results
print(result.counts)
```

Expected output:

```
{"11": 1000}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
