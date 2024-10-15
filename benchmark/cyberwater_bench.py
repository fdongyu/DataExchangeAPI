import contextlib
import random
import threading
import time
from typing import Union
from numpy import var
import requests
import uvicorn
import ModelDataExchange.clients.cyberwater.low_level_api as api

from ModelDataExchange.data_classes import SessionData, SessionID, JoinSessionData
from ModelDataExchange.clients.cyberwater.high_level_api import set_server_url, start_session
from ModelDataExchange.clients.cyberwater.low_level_api import receive_data, send_data
from ModelDataExchange.server.exchange_server import app
from ModelDataExchange.cw_cpl_indices import Vars


ITERATIONS = 10
# URL = "http://127.0.0.1:8000"
URL = "https://dataexchange.cis240199.projects.jetstream-cloud.org"
SESSION_ID = None
INVITEE_ID = 38

# If server is running on localhost
class Server(uvicorn.Server):

    def signal_handler(self):
        pass
    
    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()

        try:
            while not self.started:
                # Startup is not instantaneous. Client will fail to connect
                # if we don't wait for the server to start.
                time.sleep(1e-3)
            yield
        finally: # This is called when start_server is finished yielding
            self.should_exit = True
            thread.join()


def start_server(host_url="0.0.0.0", host_port=8000):
    """
    Server fixture for each test. Every test will start on a fresh server instance
    """

    config = uvicorn.Config(app=app, host=host_url, port=host_port)
    server = Server(config)

    with server.run_in_thread():
        yield

def run_post_command_r(command: str, data):
    
    session_id_dict = requests.post(f"{URL}/{command}", json=data.model_dump()).json().get("session_id")
    SESSION_ID = SessionID(
        source_model_id=session_id_dict.get("source_model_id"),
        destination_model_id=session_id_dict.get("destination_model_id"),
        initiator_id=session_id_dict.get("initiator_id"),
        invitee_id=session_id_dict.get("invitee_id"),
        client_id=session_id_dict.get("client_id")
    )
    return SESSION_ID

def run_post_command(command: str, data):
    requests.post(f"{URL}/{command}", json=data.model_dump())


def run_post_command_no_dump(command: str, data):
    requests.post(f"{URL}/{command}", params=data)


def run_get_command(command: str, params: dict):
    requests.get(f"{URL}/{command}", params=params)


def prepare_session(vars: int, var_sizes: list[int]):
    session_data = prepare_user(vars, var_sizes)
    
    set_server_url(URL)
    SESSION_ID = start_session(session_data)


def join_session():    
    global SESSION_ID, INVITEE_ID
    data = JoinSessionData(
        session_id=SESSION_ID, # type: ignore
        invitee_id=INVITEE_ID
    )

    session_id = requests.post(f"{URL}/join_session", json=data.model_dump()).json().get("session_id")
    return SessionID(
        source_model_id=session_id.get("source_model_id"),
        destination_model_id=session_id.get("destination_model_id"),
        initiator_id=session_id.get("initiator_id"),
        invitee_id=session_id.get("invitee_id"),
        client_id=session_id.get("client_id")
    )


def end_session(join=False):
    if join:
        requests.post(f"{URL}/end_session", json=join_session().model_dump())
    requests.post(f"{URL}/end_session", json=SESSION_ID.model_dump()) # type: ignore
    # print(result.json())

def prepare_data(var_size):    

    return [ random.random() for _ in range(var_size)]    

def setup_send_data(var_sizes: list[int]):
    prepare_session([ var for var in range(len(var_sizes))], var_sizes)
    join_session()
    prepare_data(var_sizes)

def prepare_user(num_vars: int, var_sizes: list[int]) -> Union[SessionData, list[SessionData]]:
    """
    Prepare a user for a session. If num_vars is >1, the number of variables will be num_vars
    if var_sizes is >1, a single user will be created with num_vars variables each of size 
    where var 1 has size var_sizes[0], var 2 has size var_sizes[1], etc.

    A minimum of 2 variables is used for each user. 

    Args:
        num_vars (int): The number of variables to create
        var_sizes (list[int]): The size of each variable

    Returns:
        Union[SessionData, list[SessionData]]: The session data for the user(s)
    """
    global INVITEE_ID

    if num_vars > 1 and len(var_sizes) == 1:
        return SessionData(
            source_model_id=Vars.index_ELM.value,
            destination_model_id=Vars.index_VIC5.value,
            initiator_id=35,
            invitee_id=INVITEE_ID,
            input_variables_id=[i for i in range(num_vars - 1)],
            input_variables_size=[var_sizes[0]]*num_vars,
            output_variables_id=[num_vars],
            output_variables_size=[var_sizes[0]]*num_vars
        )
    elif num_vars == 1 and len(var_sizes) > 1:
        data = []
        for i in range(len(var_sizes)):
            data.append(SessionData(
                source_model_id=Vars.index_ELM.value,
                destination_model_id=Vars.index_VIC5.value,
                initiator_id=35,
                invitee_id=INVITEE_ID,
                input_variables_id=[1],
                input_variables_size=[var_sizes[i]],
                output_variables_id=[2],
                output_variables_size=[var_sizes[i]]
            ))
        return data
    elif num_vars > 1 and len(var_sizes) > 1:
        assert len(var_sizes) == num_vars, "Number of variables must match number of sizes in prepare_user()"
        return SessionData(
                source_model_id=Vars.index_ELM.value,
                destination_model_id=Vars.index_VIC5.value,
                initiator_id=35,
                invitee_id=INVITEE_ID,
                input_variables_id=[i for i in range(num_vars - 1)],
                input_variables_size=[var_sizes[x] for x in range(len(var_sizes)-1)],
                output_variables_id=[num_vars],
                output_variables_size=[var_sizes[-1]]
            )
    else:
        return SessionData(
                source_model_id=Vars.index_ELM.value,
                destination_model_id=Vars.index_VIC5.value,
                initiator_id=35,
                invitee_id=INVITEE_ID,
                input_variables_id=[1],
                input_variables_size=[var_sizes[0]],
                output_variables_id=[2],
                output_variables_size=[var_sizes[0]]
            )


def user_helper(user: SessionData) -> tuple[SessionData, int]:
    """
    Helper function to determine the user data and variable ID to use in the benchmark function.
    
    this function was originally written to handle several casese that were not implemented
    """

    data = user
    var_id = data.output_variables_id[0] # largest one
    return data, var_id


def benchmark(function, setup_func, teardown: bool, *args):
    global ITERATIONS, URL
    results = []


    # cold start
    function(*args)

    for _ in range(ITERATIONS):
        start = time.perf_counter()
        function(*args)
        end = time.perf_counter()
        results.append(end - start)
    
    return results


def create_session_benchmark(user: SessionData):
    global SESSION_ID
    data = user_helper(user)[0]

    results = []

    for _ in range(ITERATIONS):
        start = time.perf_counter()
        SESSION_ID = run_post_command_r("create_session", data)
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results

def join_session_benchmark(user: SessionData):
    global SESSION_ID

    data = user_helper(user)[0]

    results = []

    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        start = time.perf_counter()
        join_session()
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results

def get_session_status_benchmark(user: SessionData):
    global SESSION_ID

    data = user_helper(user)[0]

    results = []

    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        start = time.perf_counter()
        api.get_session_status(URL, SESSION_ID)
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results

def get_var_flag_benchmark(user: SessionData):
    global SESSION_ID
    data, var_id = user_helper(user)

    results = []

    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        start = time.perf_counter()
        api.get_variable_flag(URL, SESSION_ID, var_id)
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results


def get_var_size_benchmark(user: SessionData):
    global SESSION_ID, URL
    data, var_id = user_helper(user)

    results = []

    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        start = time.perf_counter()
        api.get_variable_size(URL, SESSION_ID, var_id)
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results

def end_session_benchmark(user: SessionData):
    global SESSION_ID
    data = user_helper(user)[0]

    results = []

    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        start = time.perf_counter()
        end_session()
        end = time.perf_counter()
        results.append(end - start)
        end_session()

    return results


def send_data_benchmark(user: SessionData):
    global SESSION_ID

    data, var_id = user_helper(user)
    server_data = prepare_data(data.output_variables_size[0])


    results = []
    
    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        start = time.perf_counter()
        send_data(URL, SESSION_ID, var_id, server_data)
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results

def recv_data_benchmark(user: SessionData):
    global SESSION_ID
    data, var_id = user_helper(user)
    server_data = prepare_data(data.output_variables_size[0])

    results = []

    for _ in range(ITERATIONS):
        SESSION_ID = run_post_command_r("create_session", data)
        send_data(URL, SESSION_ID, var_id, server_data)
        start = time.perf_counter()
        receive_data(URL, SESSION_ID, var_id)
        end = time.perf_counter()
        results.append(end - start)
        end_session()
        end_session(True)

    return results


def run_benchmarks():
    global INVITEE_ID
    # "name, function, SessionData (size of data)

    send_data_users: list[SessionData] = prepare_user(1, [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000, 10000000000])
    default_user = prepare_user(1, [1])
    user_10 = prepare_user(10, [1])
    user_100 = prepare_user(100, [1])
    user_1000 = prepare_user(1000, [1])
    user_10000 = prepare_user(10000, [1])
    user_100000 = prepare_user(100000, [1])
    user_1000000 = prepare_user(1000000, [1])



    benchmarks = [
        ("create_session-1",      create_session_benchmark, default_user),
        ("create_session-10",     create_session_benchmark, user_10),
        ("create_session-100",    create_session_benchmark, user_100),
        ("create_session-1000",   create_session_benchmark, user_1000),
        ("create_session-10000",  create_session_benchmark, user_10000),
        ("create_session-100000", create_session_benchmark, user_100000),
        ("create_session-1000000", create_session_benchmark, user_1000000),
        ("join_session-1",      join_session_benchmark, default_user),
        ("join_session-10",     join_session_benchmark, user_10),
        ("join_session-100",    join_session_benchmark, user_100),
        ("join_session-1000",   join_session_benchmark, user_1000),
        ("join_session-10000",  join_session_benchmark, user_10000),
        ("join_session-100000", join_session_benchmark, user_100000),
        ("join_session-1000000", join_session_benchmark, user_1000000),
        ("get_session_status-1",      get_session_status_benchmark, default_user),
        ("get_session_status-10",     get_session_status_benchmark, user_10),
        ("get_session_status-100",    get_session_status_benchmark, user_100),
        ("get_session_status-1000",   get_session_status_benchmark, user_1000),
        ("get_session_status-10000",  get_session_status_benchmark, user_10000),
        ("get_session_status-100000", get_session_status_benchmark, user_100000),
        ("get_var_flag-1",      get_var_flag_benchmark, default_user),
        ("get_var_flag-10",     get_var_flag_benchmark, user_10),
        ("get_var_flag-100",    get_var_flag_benchmark, user_100),
        ("get_var_flag-1000",   get_var_flag_benchmark, user_1000),
        ("get_var_flag-10000",  get_var_flag_benchmark, user_10000),
        ("get_var_flag-100000", get_var_flag_benchmark, user_100000),
        ("get_var_flag-1000000", get_var_flag_benchmark, user_1000000),
        ("get_var_size-1",      get_var_size_benchmark, default_user),
        ("get_var_size-10",     get_var_size_benchmark, user_10),
        ("get_var_size-100",    get_var_size_benchmark, user_100),
        ("get_var_size-1000",   get_var_size_benchmark, user_1000),
        ("get_var_size-10000",  get_var_size_benchmark, user_10000),
        ("get_var_size-100000", get_var_size_benchmark, user_100000),
        ("get_var_size-1000000", get_var_size_benchmark, user_1000000),
        ("end_session-1",      end_session_benchmark, default_user),
        ("end_session-10",     end_session_benchmark, user_10),
        ("end_session-100",    end_session_benchmark, user_100),
        ("end_session-1000",   end_session_benchmark, user_1000),
        ("end_session-10000",  end_session_benchmark, user_10000),
        ("end_session-100000", end_session_benchmark, user_100000),
        ("end_session-1000000", end_session_benchmark, user_1000000),
        ("send_data-1",       send_data_benchmark, send_data_users[0]),
        ("send_data-10",      send_data_benchmark, send_data_users[1]),
        ("send_data-100",     send_data_benchmark, send_data_users[2]),
        ("send_data-1000",    send_data_benchmark, send_data_users[3]),
        ("send_data-10000",   send_data_benchmark, send_data_users[4]),
        ("send_data-100000",  send_data_benchmark, send_data_users[5]),
        ("send_data-1000000", send_data_benchmark, send_data_users[6]),
        ("send_data-10000000", send_data_benchmark, send_data_users[7]),
        ("send_data-100000000", send_data_benchmark, send_data_users[8]),
        ("send_data-1000000000", send_data_benchmark, send_data_users[9]),
        ("send_data-10000000000", send_data_benchmark, send_data_users[10]),
        ("recv_data-1",       recv_data_benchmark, send_data_users[0]),
        ("recv_data-10",      recv_data_benchmark, send_data_users[1]),
        ("recv_data-100",     recv_data_benchmark, send_data_users[2]),
        ("recv_data-1000",    recv_data_benchmark, send_data_users[3]),
        ("recv_data-10000",   recv_data_benchmark, send_data_users[4]),
        ("recv_data-100000",  recv_data_benchmark, send_data_users[5]),
        ("recv_data-1000000", recv_data_benchmark, send_data_users[6]),
        ("recv_data-10000000", recv_data_benchmark, send_data_users[7]),
        ("recv_data-100000000", recv_data_benchmark, send_data_users[8]),
        ("recv_data-1000000000", recv_data_benchmark, send_data_users[9]),
        ("recv_data-10000000000", recv_data_benchmark, send_data_users[10]),
        
    ]

    results = {}
    
    # Run benchmarks
    for benchmark in benchmarks:
        name, func, arg = benchmark
        print("Running", name)
        results[name] = func(arg)
    
    # Statistical Analysis
    stats = statistical_analysis(results)
    
    # Write results to file
    write_results(results, stats)
    

def statistical_analysis(results):
    
    # Mean, Median, Variance, Standard Deviation
    analysis = {}

    for key, value in results.items(): 
        analysis[key] = {
            "mean": sum(value) / len(value),
            "median": value[len(value) // 2],
            "variance": var(value),
            "std_dev": var(value) ** 0.5,
            "min": min(value),
            "max": max(value),
            "range": max(value) - min(value)
        }

    return analysis

def write_results(raw, stats):
    
    with open("raw_results.txt", "w") as file:
        for key in raw.keys():
            file.write(f"{key}, {','.join([str(x) for x in raw[key]])}\n")
    
    with open("statistical_results.txt", "w") as file:
        file.write("name, mean, median, variance, std_dev, min, max, range\n")
        
        for key, value in stats.items():
            file.write(f"{key}, {value['mean']}, {value['median']}, {value['variance']}, {value['std_dev']}, {value['min']}, {value['max']}, {value['range']}\n")
            



if __name__ == "__main__":
    
    if URL == "http://0.0.0.0:8000":
        start_server()
    
    run_benchmarks()