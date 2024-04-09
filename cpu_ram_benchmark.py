import subprocess
import threading
import time
import sys
import signal
import psutil
 
def signal_handler(signum, frame):
    global shutdown_flag
    shutdown_flag = True
 
def run_monitor_benchmark(binary_path, thread_index):
    global counters, pids, shutdown_flag
    process = subprocess.Popen(binary_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pids[thread_index] = process.pid
    try:
        ps_process = psutil.Process(process.pid)
        ps_process.cpu_affinity([thread_index])
    except ValueError:
        print(f"Error: CPU {thread_index} does not exist. Shutting down.")
        shutdown_flag = True
        return
 
    while not shutdown_flag:
        output = process.stdout.readline().decode().strip()
        if output == '' and process.poll() is not None:
            break
        if output:
            counters[thread_index] += 10
 
    process.terminate()
    return process.poll()
 
def benchmark_cpu_usage_delta():
    global latest_benchmark_cpu
    current_benchmark_cpu = sum(psutil.Process(p).cpu_times().user + psutil.Process(p).cpu_times().system for p in pids if p)
    delta_benchmark_cpu = 0
    if latest_benchmark_cpu:
        delta_benchmark_cpu = round((current_benchmark_cpu - latest_benchmark_cpu) * 1000)
    latest_benchmark_cpu = current_benchmark_cpu
    return delta_benchmark_cpu
 
def total_cpu_usage_delta():
    global latest_total_cpu
    current_total_cpu = psutil.cpu_times().user + psutil.cpu_times().system
    delta_total_cpu = 0
    if latest_total_cpu:
        delta_total_cpu = round((current_total_cpu - latest_total_cpu) * 1000)
    latest_total_cpu = current_total_cpu
    return delta_total_cpu
 
def update_stats(duration):
    global counters
    end_time = time.time() + duration
    while time.time() < end_time and not shutdown_flag:
        counters[num_threads] = total_cpu_usage_delta()
        counters[num_threads + 1] = benchmark_cpu_usage_delta()
        print(' '.join(str(counter) for counter in counters))
        counters = [0] * (num_threads + 2)
        time.sleep(0.999)
 
def create_binary():
    source_code = r'''
        #include <stdio.h>
        #include <stdlib.h>
        #include <time.h>
        #include <unistd.h>
 
        #define ARRAY_SIZE 100000000
        #define CHASE_ITERATIONS 10000
 
        void shuffle(int *array, size_t n) {
            if (n > 1) {
                size_t i;
                for (i = 0; i < n - 1; i++) {
                    size_t j = i + rand() / (RAND_MAX / (n - i) + 1);
                    int t = array[j];
                    array[j] = array[i];
                    array[i] = t;
                }
            }
        }
        int main() {
            srand(time(NULL));
 
            // Initialize the array with a cast for malloc
            int *array = (int *)malloc(ARRAY_SIZE * sizeof(int));
            if (array == NULL) {
                fprintf(stderr, "Failed to allocate memory\n");
                return 1;
            }
 
            for (int i = 0; i < ARRAY_SIZE; i++) {
                array[i] = i;
            }
 
            shuffle(array, ARRAY_SIZE);
 
            // Pointer chasing
            while (1) {
                int startIndex = rand() % ARRAY_SIZE;
                volatile int index = startIndex;
                for (int i = 0; i < CHASE_ITERATIONS; i++) {
                    index = array[index];
                }
                printf("1\n");
                fflush(stdout);
            }
 
            free(array);
            return 0;
        }
    '''
    # Write the C code to a file
    with open("cpu_bench_v3.c", "w") as file:
        file.write(source_code)
    compile_process = subprocess.run(["gcc", "-Ofast", "cpu_bench_v3.c", "-o", "cpu_bench_v3"], check=True)
    if compile_process.returncode != 0:
        print ("compile error")
        exit()
     
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: script.py <num_threads> <duration_in_seconds> <start_delay>")
        sys.exit(1)
         
    create_binary()
    num_threads = int(sys.argv[1])
    duration = int(sys.argv[2])
    retardant = int(sys.argv[3])
         
    binary_path = "./cpu_bench_v3"
    counters = [0] * (num_threads + 2)
    latest_total_cpu = 0
    latest_benchmark_cpu = 0
    pids = [0] * num_threads
    shutdown_flag = False
 
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
     
    # print headers
    print(" ".join(f"Thread-{i}" for i in range(num_threads)) + " Total-CPU Benchmark-CPU")
 
    stat_thread = threading.Thread(target=update_stats, args=(duration,))
    stat_thread.start()
 
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=run_monitor_benchmark, args=(binary_path, i))
        threads.append(thread)
        thread.start()
        time.sleep(retardant)
 
    for thread in threads:
        thread.join()
    stat_thread.join()
