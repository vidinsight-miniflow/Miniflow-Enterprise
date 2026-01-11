from threading import Event
from multiprocessing import cpu_count
from .type_controller import TypeController


class ProcessController:
    def __init__(self, output_queue, input_queue, logger, iob_task_limit: int, cb_task_limit: int, os: bool):
        self.output_queue = output_queue
        self.input_queue = input_queue
        self.max_process_count = cpu_count() - 1
        self.started = False
        self.shutdown_event = Event()
        self.os = os
        self.cb_task_limit = cb_task_limit
        self.iob_task_limit = iob_task_limit
        self.logger = logger
        
        self.logger.info(f"[PROCESS CONTROLLER] Initializing with max_process_count={self.max_process_count}")
        self.logger.info(f"[PROCESS CONTROLLER] CPU-Bound: 1 process, task_limit={cb_task_limit}")
        self.logger.info(f"[PROCESS CONTROLLER] IO-Bound: {self.max_process_count - 1} processes, task_limit={iob_task_limit}")
        
        self.cb_controller = TypeController(output_queue=self.output_queue, process_count=1, task_limit=cb_task_limit,
                                            os=self.os, controller_type="CPU-Bound")
        self.iob_controller = TypeController(output_queue=self.output_queue, process_count=self.max_process_count - 1,
                                             task_limit=iob_task_limit, os=self.os, controller_type="IO-Bound")
        
        self.logger.info("[PROCESS CONTROLLER] Type controllers initialized")

    def start(self):
        if self.started:
            return False, "[PROCESS CONTROLLER] ProcessController already started"

        success, message = self.cb_controller.start()
        if not success:
            self.logger.error(message)
            return False, message

        success, message = self.iob_controller.start()
        if not success:
            self.logger.error(message)
            return False, message

        self.started = True
        return True, "[PROCESS CONTROLLER] ProcessController started successfully"

    def get_cb_ps_info(self):
        return self.cb_controller.get_ps_info()

    def get_iob_ps_info(self):
        return self.iob_controller.get_ps_info()

    def create_thread(self, item):
        if not self._check_retry(item):
            process_type = item.get("process_type")
            self.logger.info(f"[PROCESS CONTROLLER] Item process_type: {process_type}")
            
            if process_type == "cb":
                self.logger.info("[PROCESS CONTROLLER] Using CPU-Bound controller")
                success, message = self.cb_controller.create_thread(item)

                if success:
                    self.logger.info("[PROCESS CONTROLLER] CPU-Bound task created successfully")
                    return True
                else:
                    self.logger.error(message)
                    self.logger.warning("[PROCESS CONTROLLER] CPU-Bound controller busy, requeueing")
                    self.input_queue.put(item)
                    return False

            elif process_type == "iob":
                self.logger.info("[PROCESS CONTROLLER] Using IO-Bound controller")
                success, message = self.iob_controller.create_thread(item)
                if success:
                    self.logger.info("[PROCESS CONTROLLER] IO-Bound task created successfully")
                    return True
                else:
                    self.logger.error(message)
                    self.logger.warning("[PROCESS CONTROLLER] IO-Bound controller busy, requeueing")
                    self.input_queue.put(item)
                    return False

            else:
                self.logger.error(f"[PROCESS CONTROLLER] Unknown process_type: {process_type}, failing task")
                item["result_data"] = f"Unknown process_type: {process_type}"
                item["status"] = "FAILED"
                self.output_queue.put(item)
                return False

        else:
            self.logger.warning("[PROCESS CONTROLLER] Retry limit exceeded")
            item["result_data"] = "Retry Limit Exceeded"
            item["status"] = "FAILED"
            self.output_queue.put(item)
            return False

    def _check_retry(self, item):
        if item.get("retry") is not None:
            item["retry"] += 1
            return item.get("retry") > item.get("max_retries")

        else:
            item["retry"] = 0
            return False

    def shutdown(self):
        """Graceful shutdown"""
        self.shutdown_event.set()

        self.cb_controller.shutdown()
        self.iob_controller.shutdown()
        return True