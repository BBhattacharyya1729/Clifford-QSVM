from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
import numpy as np
import stim

def Cliffordize(circuit):
    """
    Take a circuit and round all the parameters to nearest multiples of π/2
    circuit (QuantumCircuit): The circuit that will be rounded
    
    Returns:
    (QuantumCircuit): The circuit with all rotation gates rounded
    """
    dag = circuit_to_dag(circuit)
    for node in dag.op_nodes():
        if node.name == "h":
            qc_loc = QuantumCircuit(1)
            qc_loc.rz(np.pi , 0)
            qc_loc.ry(np.pi/2 , 0)
            qc_loc_instr = qc_loc.to_instruction()
            dag.substitute_node(node, qc_loc_instr, inplace = True)
        if node.name == "ry":
            angle = float(node.op.params[0])
            qc_loc = QuantumCircuit(1)
            qc_loc.ry(np.pi/2 * np.round(2/np.pi * angle ), 0)
            qc_loc_instr = qc_loc.to_instruction()
            dag.substitute_node(node, qc_loc_instr, inplace = True)
        elif node.name == 'rz':
            angle = float(node.op.params[0])
            qc_loc = QuantumCircuit(1)
            qc_loc.rz(np.pi/2 * np.round(2/np.pi * angle ), 0)
            qc_loc_instr = qc_loc.to_instruction()
            dag.substitute_node(node, qc_loc_instr, inplace = True)
    return dag_to_circuit(dag).decompose()


def modify(qc,st,qubit,parameter):
    '''
    Add a specified operator to existing circuit
    (QuantumCircuit) qc: Quantum Circuit to modify
    (String) st: String for operator
    (Int) qubit: qubit index
    (Parameter): the parameter
    
    Returns None
    '''
    N=qc.num_qubits
    param = False
    local=True
    gate = True
    s="".join(i for i in st)
    
    if(s[:3]== '000'):
         qc.h(0)
    elif(s[:3]== '001'):
        qc.cnot(qubit, (qubit+1) % N)
        local=False
    elif(s[:3]== '101'):
        qc.cnot(qubit, (qubit+1) % N)
        local=False
    elif(s[:3] == '101' and s[-3:] != '000'):
        qc.rx(np.pi/8 * int(s[-3:],2) * parameter ,qubit)
        param= True
    elif(s[:3] == '110' and s[-3:] != '000'):
        qc.ry(np.pi/8 * int(s[-3:],2) * parameter ,qubit)
        param= True
    elif(s[:3] == '111' and s[-3:] != '000'):
        qc.rz(np.pi/8 * int(s[-3:],2) * parameter,qubit)
        param= True
    else:
        gate = False
    return param,local,gate


def string_to_circuit(s, M, x_len):
    """
    Convert an array of 0's and 1's into a circuit
    
    (Iterable[String]) s: Sequence of bits
    (Int) M: number of qubits
    (Int) x_len: Dimension of data
    """
    X  = ParameterVector('x',x_len)
    qc = QuantumCircuit(M)
    N = len(s)//(6*M)
    layers = np.array([s[6*i:6*i+6] for i in range(len(s)//6)],dtype=str)
    layers = np.split(layers,N)
    
    index = 0
    gates = 0
    non_locals = 0
    for n,instr in enumerate(layers):
        for i in range(M):
            s=instr[i]
            param,local,gate=modify(qc,s,i,X[index])
            if(gate):
                gates+=1
                if(param):
                    index = (index+1) % x_len
                if(not local):
                    non_locals+=1
    return qc,gates,non_locals