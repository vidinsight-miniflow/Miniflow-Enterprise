import json, psutil, time
from multiprocessing import Pipe
from ..process import BaseProcess
from threading import Thread, Lock, Event


class TypeController:
    def __init__(self, output_queue, os: bool, process_count: int, task_limit: int, controller_type: str):
        self.output_queue = output_queue
        self.priority = -19 if os else psutil.HIGH_PRIORITY_CLASS  # self._unix_process_classes() if os else self._nt_process_classes()
        self.process_count = process_count
        self.task_limit = task_limit
        self.controller_type = controller_type
        self._set_options()

    def _set_options(self):
        self.active_processes = []
        self.scaler_thread = None
        self.started = False
        self.shutdown_event = Event()
        self.process_lock = Lock()

    def start(self):
        if self.started:
            raise RuntimeError(f"[TYPE CONTROLLER {self.controller_type}] Controller already started")

        self.started = True

        success, message = self._start_processes(self.process_count)
        if not success:
            return False, message

        self._start_thread_counter()
        return True, f"[TYPE CONTROLLER {self.controller_type}] Successfully started {self.process_count} processes"

    def _start_processes(self, count):
        for i in range(count):
            try:
                cmd_parent_conn, cmd_child_conn = Pipe()
                health_parent_conn, health_child_conn = Pipe()
                process = BaseProcess(cmd_child_conn, health_child_conn, self.output_queue)
                process.start()
                # Priority ayarı kritik değil - sadece warning log'la
                success, message = self._set_process_priority(process.process.pid, self.priority)
                if not success:
                    # Priority hatası durumunda sadece warning log'la, process başlatıldı
                    print(f"[WARNING] {message}")
                self.active_processes.append({
                    'name': f'{self.controller_type}-{i}',
                    'pid': process.process.pid,
                    'process': process,
                    'cmd_pipe': cmd_parent_conn,
                    'health_pipe': health_parent_conn,
                    'thread_count': 0
                })
            except Exception as e:
                return False, f"[TYPE CONTROLLER {self.controller_type}] FAILED to start process {i}: {str(e)}"

        return True, f"[TYPE CONTROLLER {self.controller_type}] Successfully started {len(self.active_processes)} processes"

    def new_process(self):
        self._start_processes(1)

    def get_ps_info(self):
        ps_info_list = []

        for process in self.active_processes:
            ps_info_list.append({'name': process['name'], 'pid': process['pid'], 'thread_count': process['thread_count']})

        return ps_info_list

    def _get_next_process(self):
        
        if not self.active_processes:
            return None, f"[TYPE CONTROLLER {self.controller_type}] No active processes available"

        available_processes = [p for p in self.active_processes if p['thread_count'] < self.task_limit]

        selected_process = min(
            (p for p in self.active_processes if p['thread_count'] < self.task_limit),
            key=lambda p: p['thread_count'],
            default=None
        )

        if selected_process:
            message = f"[TYPE CONTROLLER {self.controller_type}] Selected process: pid={selected_process['pid']}, thread_count={selected_process['thread_count']}"
        else:
            message = f"[TYPE CONTROLLER {self.controller_type}] No process available under task limit"

        return selected_process, message

    def create_thread(self, item: json):
        process, message = self._get_next_process()

        if process is None:
            return False, f"[TYPE CONTROLLER {self.controller_type}] No available process found"

        command_data = {
            "command": "start_thread",
            "data": "src.miniflow.engine.process.modules.python_runner.python_runner",
            "args": (item,),
            "kwargs": {}
        }
        process.get("cmd_pipe").send(command_data)
        return True, f"[TYPE CONTROLLER {self.controller_type}] Command sent to process {process['pid']}"

    def shutdown(self):
        self.shutdown_event.set()

        for p in self.active_processes:
            try:
                p['cmd_pipe'].send({"command": "shutdown"})
                p['process'].shutdown()
            except Exception as e:
                return False, f"[TYPE CONTROLLER {self.controller_type}] Error shutting down process: {e}"

    def _get_process_thread_counts(self):
        with self.process_lock:
            for proc_dict in self.active_processes:
                try:
                    proc_dict['health_pipe'].send({"command": "get_thread_count"})
                    if proc_dict['health_pipe'].poll(0.05):
                        resp = proc_dict['health_pipe'].recv()
                        proc_dict['thread_count'] = resp.get("thread_count", 0)
                    else:
                        proc_dict['thread_count'] = 0
                except Exception as e:
                    print(f"Error getting thread count: {e}")
                    proc_dict['thread_count'] = 0

    def _thread_count_updater(self):
        while not self.shutdown_event.is_set():
            self._get_process_thread_counts()
            time.sleep(0.2)

    def _start_thread_counter(self):
        self.scaler_thread = Thread(target=self._thread_count_updater, daemon=True)
        self.scaler_thread.start()

    def _set_process_priority(self, pid: int, priority):
        try:
            ps_process = psutil.Process(pid)
            ps_process.nice(priority)
            return True, f"[TYPE CONTROLLER {self.controller_type}] Priority set successfully for PID {pid}: {priority}"
        except (psutil.AccessDenied, PermissionError) as e:
            return False, f"[TYPE CONTROLLER {self.controller_type}] Priority access denied for PID {pid} (normal): {e}"
        except Exception as e:
            return False, f"[TYPE CONTROLLER {self.controller_type}] Priority setting error for PID {pid}: {e}"

    def _nt_process_classes(self):
        """Windows process priority classes"""
        return [psutil.IDLE_PRIORITY_CLASS, psutil.BELOW_NORMAL_PRIORITY_CLASS,
                psutil.NORMAL_PRIORITY_CLASS, psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                psutil.HIGH_PRIORITY_CLASS, psutil.REALTIME_PRIORITY_CLASS]

    def _unix_process_classes(self):
        """Unix based systems process priority range (-20 max priority, 20 min priority)"""
        return [i for i in range(-20, 21)]