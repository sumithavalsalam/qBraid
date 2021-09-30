import qbraid
from IPython.core.display import HTML, display
from pymongo import MongoClient
from time import time
from tqdm.notebook import tqdm


def _get_device_data(query):
    """Internal :meth:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-4 list containing the device provider, name, qbraid_id,
    and status.
    """
    # Hard-coded authentication to be replaced with API call
    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "qbraid-sdk?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    cursor = collection.find(query)
    device_data = []
    tot_dev = 0
    ref_dev = 0
    tot_lag = 0
    for document in cursor:
        qbraid_id = document["qbraid_id"]
        name = document["name"]
        provider = document["provider"]
        status_refresh = document["status_refresh"]
        timestamp = time()
        lag = 0 if status_refresh == -1 else timestamp - status_refresh
        if lag > 3600:
            print("\r", "Auto-refreshing device status" + "." * tot_dev, end="")
            device = qbraid.device_wrapper(qbraid_id)
            status = device.status
            collection.update_one(
                {"qbraid_id": qbraid_id},
                {"$set": {"status": status, "status_refresh": timestamp}},
                upsert=False
            )
            ref_dev += 1
        else:
            status = document["status"]
        tot_dev += 1
        tot_lag += lag
        device_data.append([provider, name, qbraid_id, status])
    cursor.close()
    client.close()
    device_data.sort()
    if ref_dev > 0:
        print(f"Auto-refreshed status for {ref_dev} devices")
    lag_minutes, _ = divmod(tot_lag / tot_dev, 60)
    return device_data, int(lag_minutes)


def refresh_devices():
    """Refreshes device status, seen in :func:`~qbraid.get_devices` output.
    Runtime ~20 seconds, with progress given by blue status bar."""

    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "qbraid-sdk?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    cursor = collection.find({})
    pbar = tqdm(total=35, leave=False)
    for document in cursor:
        if document["status_refresh"] != -1:
            qbraid_id = document["qbraid_id"]
            device = qbraid.device_wrapper(qbraid_id)
            status = device.status
            collection.update_one(
                {"qbraid_id": qbraid_id},
                {"$set": {"status": status, "status_refresh": time()}},
                upsert=False
            )
        pbar.update(1)
    pbar.close()
    cursor.close()
    client.close()


def get_devices(query=None):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID. Each device also has a status given by a solid green bubble or a hollow
    red bubble, indicating that the device is online or offline, respectively. You can narrow your
    device search by supplying a dictionary containing the desired criteria. Available filters
    include but are not limited to:

    * name (str)
    * vendor (str): AWS | IBM | Google
    * provider (str): AWS | IBM | Google | D-Wave | IonQ | Rigetti
    * type (str): QPU | Simulator
    * qubits (int)
    * paradigm (str): gate-based | quantum-annealer
    * requires_cred (bool): true | false
    * status (str): ONLINE | OFFLINE

    Here are a few example ``get_devices`` arguments using the above filters:

    .. code-block:: python

        from qbraid import get_devices

        # Search for gate-based devices provided by Google that are online/available
        get_devices({"paradigm": "gate-based", "provider": "Google", "status": "ONLINE"})

        # Search for QPUs with at least 5 qubits available through AWS or IBM
        get_devices({"type": "QPU", "qubits": {"$gte": 5}, "vendor": {"$in": ["AWS", "IBM"]}})

        # Search for open-access simulators that have "Unitary" contained in their name
        get_devices({"type": "Simulator", "name": {"$regex": "Unitary"}, "requires_cred": False})

    For a complete list of search operators, see
    `Query Selectors`<https://docs.mongodb.com/manual/reference/operator/query/#query-selectors>.
    To refresh the device status column, call :func:`~qbraid.refresh_devices`, and then
    re-run :func:`~qbraid.get_devices`. The bottom-right corner of the ``get_devices`` table
    indicates time since the last status refresh. Device status is auto-refreshed every hour.

    Args:
        query (optional, dict): a dictionary containing any filters to be applied.

    """

    input_query = {} if query is None else query
    device_data, lag = _get_device_data(input_query)
    msg = "All status up-to-date" if lag == 0 else f"Avg status lag ~{lag} min"

    html = """<h3>Supported Devices</h3><table><tr>
    <th style='text-align:left'>Provider</th>
    <th style='text-align:left'>Name</th>
    <th style='text-align:left'>qBraid ID</th>
    <th style='text-align:left'>Status</th></tr>
    """

    online = "<span style='color:green'>●</span>"
    offline = "<span style='color:red'>○</span>"

    for data in device_data:
        if data[3] == "ONLINE":
            status = online
        else:
            status = offline

        html += f"""<tr>
        <td style='text-align:left'>{data[0]}</td>
        <td style='text-align:left'>{data[1]}</td>
        <td style='text-align:left'><code>{data[2]}</code></td>
        <td>{status}</td></tr>
        """

    if len(device_data) == 0:
        html += (
            "<tr><td colspan='4'; style='text-align:center'>No results matching "
            "given criteria</td></tr>"
        )
    else:
        html += f"<tr><td colspan='4'; style='text-align:right'>{msg}</td></tr>"

    html += "</table>"

    return display(HTML(html))
