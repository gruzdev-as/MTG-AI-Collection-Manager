from inference.worker import InferenceWorker

if __name__ == "__main__":
    worker = InferenceWorker()
    worker.worker_loop()
