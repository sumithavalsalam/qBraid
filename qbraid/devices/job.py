# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/providers/job.py

"""Job abstract interface."""

from abc import abstractmethod
from typing import Callable, Optional
from .device import DeviceWrapper
from .wrapper import QbraidJobWrapper


class JobWrapper(QbraidJobWrapper):
    """Class to handle jobs."""

    _async = True

    def __init__(self, vendor_jlo) -> None:
        """Initializes the asynchronous job.
        Args:
            vendor_jlo: a job-like object used to run circuits.
        """
        self.vendor_jlo = vendor_jlo  # vendor job-like object
        self._device = None  # to be set after instantiation

    @property
    def device(self) -> DeviceWrapper:
        """Return the :class:`~qbraid.devices.device.DeviceWrapper` where this job was executed."""
        if self._device is None:
            raise SystemError("device property of JobWrapper object is None")
        return self._device

    @property
    @abstractmethod
    def job_id(self) -> str:
        """Return a unique id identifying the job."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> dict:
        pass

    @abstractmethod
    def done(self) -> bool:
        """Return whether the job has successfully run."""
        pass

    @abstractmethod
    def running(self) -> bool:
        """Return whether the job is actively running."""
        pass

    @abstractmethod
    def cancelled(self) -> bool:
        """Return whether the job has been cancelled."""
        pass

    @abstractmethod
    def in_final_state(self) -> bool:
        """Return whether the job is in a final job state such as ``DONE`` or ``ERROR``."""
        pass

    @abstractmethod
    def wait_for_final_state(
            self, timeout: Optional[float] = None, wait: float = 5,
            callback: Optional[Callable] = None
    ) -> None:
        """Poll the job status until it progresses to a final state such as ``DONE`` or ``ERROR``.
        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            wait: Seconds between queries.
            callback: Callback function invoked after each query.
                The following positional arguments are provided to the callback function:
                * job_id: Job ID
                * job_status: Status of the job from the last query
                * job: This BaseJob instance
                Note: different subclass might provide different arguments to the callback function.
        Raises:
            JobError: If the job does not reach a final state before the specified timeout.
        """
        pass

    @abstractmethod
    def submit(self):
        """Submit the job to the device for execution."""
        pass

    @abstractmethod
    def result(self):
        """Return the results of the job."""
        pass

    def cancel(self):
        """Attempt to cancel the job."""
        raise NotImplementedError

    @abstractmethod
    def status(self):
        """Return the status of the job, among the values of ``JobStatus``."""
        pass