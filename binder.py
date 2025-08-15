import docker
import os
import time
import threading
import signal
import sys
from datetime import datetime
class DockerLogCollector:
    def __init__(self):
        self.client = docker.from_env()
        #self.log_dir = "{path}"
        self.running = True
        self.threads = []
        os.makedirs(self.log_dir, exist_ok=True)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    def signal_handler(self, signum, frame):
        self.running = False
        sys.exit(0)
    def log_container(self, container):
        container_name = container.name
        log_file = os.path.join(self.log_dir, f"{container_name}.log")  
        try:
            for log in container.logs(stream=True, follow=True, timestamps=True):
                if not self.running:
                    break
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_line = f"{timestamp} [{container_name}] {log.decode('utf-8').strip()}\n"
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
        except Exception as e:
    def start_monitoring(self):
        while self.running:
            try:
                containers = self.client.containers.list()
                current_containers = {c.name for c in containers}
                running_threads = {t.name for t in self.threads if t.is_alive()}
                for container in containers:
                    if container.name not in running_threads:
                        thread = threading.Thread(
                            target=self.log_container,
                            args=(container,),
                            name=container.name,
                            daemon=True
                        )
                        thread.start()
                        self.threads.append(thread)
                        print(f"Started monitoring: {container.name}")
                self.threads = [t for t in self.threads if t.is_alive()]
                time.sleep(30)
            except Exception as e:
                time.sleep(10)
if __name__ == "__main__":
    collector = DockerLogCollector()
    try:
        collector.start_monitoring()
    except KeyboardInterrupt:
        collector.running = False
