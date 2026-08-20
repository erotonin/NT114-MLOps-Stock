from kfp import dsl
from kfp import compiler

import os

# Define the base docker image built from Dockerfile.training
# Lấy image từ Github Action pass qua. Mặc định là stock-trainer:latest nếu test thủ công.
BASE_IMAGE = os.environ.get('TRAINER_IMAGE', 'stock-trainer:latest')

@dsl.container_component
def train_stock_model(
    symbol: str
):
    """
    KFP Component to run the stock predictor training container
    """
    return dsl.ContainerSpec(
        image=BASE_IMAGE,
        command=["python", "src/training/final_ensemble_train.py"],
        args=["--symbol", symbol]
    )

@dsl.pipeline(
    name="stock-prediction-training-pipeline",
    description="Trains the ensemble models for multiple stock symbols concurrently."
)
def stock_training_pipeline(
    symbols: list = ["VNM", "VCB", "HPG", "FPT"]
):
    # Iterate over symbols to launch parallel training tasks
    with dsl.ParallelFor(symbols) as item:
        train_task = train_stock_model(symbol=item)
        train_task.set_env_variable('MLFLOW_TRACKING_URI', os.environ.get('MLFLOW_TRACKING_URI', ''))
        train_task.set_env_variable('AWS_ACCESS_KEY_ID', os.environ.get('AWS_ACCESS_KEY_ID', ''))
        train_task.set_env_variable('AWS_SECRET_ACCESS_KEY', os.environ.get('AWS_SECRET_ACCESS_KEY', ''))
        train_task.set_env_variable('AWS_SESSION_TOKEN', os.environ.get('AWS_SESSION_TOKEN', ''))
        train_task.set_env_variable('AWS_REGION', os.environ.get('AWS_REGION', 'us-east-1'))
        # Tối ưu CPU cho PyTorch/LightGBM khi chạy trong container
        train_task.set_env_variable('OMP_NUM_THREADS', '2')
        train_task.set_env_variable('MKL_NUM_THREADS', '2')
        # Set CPU và Memory limits
        train_task.set_cpu_limit('1')
        train_task.set_memory_limit('4G')

if __name__ == '__main__':
    # Compile the pipeline definition into a YAML file
    compiler.Compiler().compile(
        pipeline_func=stock_training_pipeline,
        package_path='pipeline.yaml'
    )
    print("Pipeline successfully compiled to pipeline.yaml")
