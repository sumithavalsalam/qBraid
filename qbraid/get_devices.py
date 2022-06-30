"""
Module to retrieve, update, and display information about devices
supported by the qBraid SDK.

"""
# pylint: disable=consider-using-f-string

# from time import time
from datetime import datetime
from typing import Optional

from IPython.display import HTML, clear_output, display

from .api import ApiError, QbraidSession
from .display_utils import running_in_jupyter, update_progress_bar
from .wrappers import device_wrapper


def refresh_devices():
    """Refreshes status for all qbraid supported devices. Requires credential for each vendor."""

    session = QbraidSession()
    devices = session.get("/public/lab/get-devices", params={}).json()
    count = 0
    num_devices = len(devices)  # i.e. number of iterations
    # time_estimate = num_devices * 1.1  # estimated time for ~0.9 iters/s
    # start = time()
    for document in devices:
        progress = count / num_devices
        # elapsed_sec = int(time_estimate - (time() - start))
        # stamp = f"{max(1, elapsed_sec)}s" if count > 0 else "1m"
        # time_step = f"{stamp} remaining"
        update_progress_bar(progress)
        if document["statusRefresh"] is not None:  # None => internally not available at moment
            qbraid_id = document["qbraid_id"]
            device = device_wrapper(qbraid_id)
            status = device.status.name
            session.put("/lab/update-device", data={"qbraid_id": qbraid_id, "status": status})
        count += 1
    print()


def _get_device_data(query):
    """Internal :func:`~qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-4 list containing the device provider, name, qbraid_id,
    and status.
    """
    session = QbraidSession()

    # get-devices must be a POST request with kwarg `json` (not `data`) to
    # encode the query. This is because certain queries contain regular
    # expressions which cannot be encoded in GET request `params`.
    devices = session.post("/public/lab/get-devices", json=query).json()

    if isinstance(devices, str):
        raise ApiError(devices)
    device_data = []
    tot_dev = 0
    tot_lag = 0
    for document in devices:
        qbraid_id = document["qbraid_id"]
        name = document["name"]
        provider = document["provider"]
        status_refresh = document["statusRefresh"]
        timestamp = datetime.utcnow()
        lag = 0
        if status_refresh is not None:
            format_datetime = str(status_refresh)[:10].split("-") + str(status_refresh)[
                11:19
            ].split(":")
            format_datetime_int = [int(x) for x in format_datetime]
            mk_datime = datetime(*format_datetime_int)
            lag = (timestamp - mk_datime).seconds
        status = document["status"]
        tot_dev += 1
        tot_lag += lag
        device_data.append([provider, name, qbraid_id, status])
    if tot_dev == 0:
        return [], 0  # No results matching given criteria
    device_data.sort()
    lag_minutes, _ = divmod(tot_lag / tot_dev, 60)
    return device_data, int(lag_minutes)


def _display_basic(data, msg):
    if len(data) == 0:
        print(msg)
    else:
        print(f"{msg}\n")
        print("{:<35} {:<15}".format("Device ID", "Status"))
        print("{:<35} {:<15}".format("-" * 9, "-" * 6))
        for _, _, device_id, status in data:
            print("{:<35} {:<15}".format(device_id, status))


def _display_jupyter(data, msg, align=None):

    clear_output(wait=True)

    align = "right" if align is None else align

    html = """<h3>Supported Devices</h3><table><tr>
    <th style='text-align:left'>Provider</th>
    <th style='text-align:left'>Name</th>
    <th style='text-align:left'>qBraid ID</th>
    <th style='text-align:left'>Status</th></tr>
    """

    online = "<span style='color:green'>●</span>"
    offline = "<span style='color:red'>○</span>"

    for provider, name, qbraid_id, status_str in data:
        if status_str == "ONLINE":
            status = online
        else:
            status = offline

        html += f"""<tr>
        <td style='text-align:left'>{provider}</td>
        <td style='text-align:left'>{name}</td>
        <td style='text-align:left'><code>{qbraid_id}</code></td>
        <td>{status}</td></tr>
        """

    html += f"<tr><td colspan='4'; style='text-align:{align}'>{msg}</td></tr>"

    html += "</table>"

    return display(HTML(html))


def get_devices(filters: Optional[dict] = None, refresh: bool = False):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID. Each device also has a status given by a solid green bubble or a hollow
    red bubble, indicating that the device is online or offline, respectively. You can narrow your
    device search by supplying a dictionary containing the desired criteria.

    **Request Syntax:**

    .. code-block:: python

        get_devices(
            filters={
                'name': 'string',
                'vendor': 'AWS'|'IBM'|'Google',
                'provider: 'AWS'|'IBM'|'Google'|'D-Wave'|'IonQ'|'Rigetti'|'OQC',
                'type': 'QPU' | 'Simulator',
                'numberQubits': 123,
                'paradigm': 'gate-based'|'quantum-annealer',
                'requiresCred': True|False,
                'status': 'ONLINE'|'OFFLINE'
            }
        )

    **Filters:**

        * **name** (str): Name quantum device name
        * **vendor** (str): Company whose software facilitaces access to quantum device
        * **provider** (str): Company providing the quantum device
        * **type** (str): If the device is a quantum simulator or hardware
        * **numberQubits** (int): The number of qubits in quantum device
        * **paradigm** (str): The quantum model through which the device operates
        * **requiresCred** (bool): Whether the device requires credentialed access
        * **status** (str): Availability of device

    **Examples:**

    .. code-block:: python

        from qbraid import get_devices

        # Search for gate-based devices provided by Google that are online/available
        get_devices(
            filters={"paradigm": "gate-based", "provider": "Google", "status": "ONLINE"}
        )

        # Search for QPUs with at least 5 qubits that are available through AWS or IBM
        get_devices(
            filters={"type": "QPU", "numberQubits": {"$gte": 5}, "vendor": {"$in": ["AWS", "IBM"]}}
        )

        # Search for open-access simulators that have "Unitary" contained in their name
        get_devices(
            filters={"type": "Simulator", "name": {"$regex": "Unitary"}, "requiresCred": False}
        )

    For a complete list of search operators, see `Query Selectors`__. To refresh the device
    status column, call :func:`~qbraid.get_devices` with ``refresh=True`` keyword argument.
    The bottom-right corner of the device table indicates time since the last status refresh.

    .. __: https://docs.mongodb.com/manual/reference/operator/query/#query-selectors

    Args:
        filters: A dictionary containing any filters to be applied.
        refresh: If True, calls :func:`~qbraid.refresh_devices` before execution.

    """
    if refresh:
        refresh_devices()
    query = {} if filters is None else filters
    device_data, lag = _get_device_data(query)

    if len(device_data) == 0:
        align = "center"
        msg = "No results matching given criteria"
    else:
        align = "right"
        hours, minutes = divmod(lag, 60)
        min_10, _ = divmod(minutes, 10)
        min_display = min_10 * 10
        if hours > 0:
            if minutes > 30:
                msg = f"Device status updated {hours}.5 hours ago"
            else:
                hour_s = "hour" if hours == 1 else "hours"
                msg = f"Device status updated {hours} {hour_s} ago"
        else:
            if minutes < 10:
                min_display = minutes
            msg = f"Device status updated {min_display} minutes ago"

    if not running_in_jupyter():
        _display_basic(device_data, msg)
    else:
        _display_jupyter(device_data, msg, align=align)