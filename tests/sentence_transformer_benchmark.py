import time
import tracemalloc
from tqdm import tqdm  # Import tqdm for progress bar
from sentence_transformers import SentenceTransformer

def benchmark_model(model_name, sentences, iterations=10):
    # Load the model
    model = SentenceTransformer(model_name)
    
    # Warm up to load any necessary components
    model.encode(["Warm-up sentence"])

    # Start memory tracking
    tracemalloc.start()

    # Record start time
    start_time = time.time()

    # Encode sentences multiple times to measure average performance
    for _ in tqdm(range(iterations), desc=f"Benchmarking {model_name}"):
        embeddings = model.encode(sentences, show_progress_bar=False)
    
    # Record end time
    end_time = time.time()
    
    # Stop memory tracking
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Calculate metrics
    total_time = end_time - start_time
    avg_time_per_call = total_time / iterations
    memory_usage_peak = peak / 10**6  # Convert bytes to MB

    print(f"\nModel: {model_name}")
    print(f"Average Time per Iteration: {avg_time_per_call:.4f} seconds")
    print(f"Peak Memory Usage: {memory_usage_peak:.4f} MB")
    print(f"Embedding Dimension: {len(embeddings[0])}")

    return avg_time_per_call, memory_usage_peak

if __name__ == "__main__":
    sentences = [
        "This is a test sentence.",
        "Another sentence follows this one.",
        "Sentence Transformers provide embeddings for these sentences."
    ]

    # List of models to benchmark
    models = [
        'all-MiniLM-L6-v2',
        'all-mpnet-base-v2',
        'paraphrase-xlm-r-multilingual-v1',
        'intfloat/multilingual-e5-large-instruct',
        # Add more models here if desired
    ]

    for model_name in models:
        print("\n" + "="*50)
        benchmark_model(model_name, sentences)