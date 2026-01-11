from threading import Event, Lock, Thread
import time


class QueueController:
    def __init__(self, input_queue, process_controller):
        self.input_queue = input_queue
        self.process_controller = process_controller
        self.started = False
        self.shutdown_event = Event()
        self.process_lock = Lock()

    def start(self):
        if self.started:
            return False, "[QUEUE CONTROLLER] QueueController already started"

        watcher_thread = Thread(target=self.watch_input_queue, daemon=True)
        watcher_thread.start()

        self.started = True
        return True, "[QUEUE CONTROLLER] QueueController started successfully"

    def watch_input_queue(self):
        while not self.shutdown_event.is_set():
            try:
                item = self.input_queue.get_with_timeout(timeout=1.0)
                if item is not None:
                    with self.process_lock:
                        print(f"[QUEUE CONTROLLER] Processing item: execution_id={item.get('execution_id')}, process_type={item.get('process_type')}")
                        print(f"[QUEUE CONTROLLER] Item details: {item}")
                        
                        if self.process_controller.create_thread(item):
                            print("[QUEUE CONTROLLER] Task Created Successfully")
                        else:
                            print("[QUEUE CONTROLLER] Task Creation Failed")
                            print(f"[QUEUE CONTROLLER] Failed item: execution_id={item.get('execution_id')}, process_type={item.get('process_type')}")

                        time.sleep(1)

            except Exception as e:
                print(f"[QUEUE CONTROLLER] Input watcher error: {e}")

    def shutdown(self):
        self.shutdown_event.set()