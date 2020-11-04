import os

from qiskit import IBMQ, execute
from qiskit.test.reference_circuits import ReferenceCircuits


def run_job(backend):
    job = execute(ReferenceCircuits.bell(), backend=backend)
    job.wait_for_final_state()


def main():
    provider = IBMQ.load_account()

    hgp = os.getenv('QE_HGP', None)
    if hgp:
        hgp = hgp.split('/')
        provider = IBMQ.get_provider(hub=hgp[0], group=hgp[1], project=hgp[2])

    backend = provider.get_backend('ibmq_qasm_simulator')
    for i in range(200):
        print(f"submitting job {i}")
        run_job(backend)


if __name__ == '__main__':
    main()
