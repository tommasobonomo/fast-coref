import os
from os import path
import logging
from omegaconf import OmegaConf
import hydra
import hashlib
import json
import wandb

from experiment import Experiment

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def get_model_name(config):
	masked_copy = OmegaConf.masked_copy(config, ['datasets', 'model', 'trainer', 'optimizer'])
	encoded = json.dumps(OmegaConf.to_container(masked_copy), sort_keys=True).encode()
	hash_obj = hashlib.md5()
	hash_obj.update(encoded)

	model_hash = str(hash_obj.hexdigest())
	if len(config.datasets) > 1:
		dataset_name = 'joint'
	else:
		dataset_name = list(config.datasets.keys())[0]

	model_name = f"{dataset_name}_{model_hash}"
	return model_name


@hydra.main(config_path="conf", config_name="config")
def main(config):
	if config.paths.model_name is None:
		model_name = get_model_name(config)
	else:
		model_name = config.paths.model_name
	config.paths.model_dir = path.join(
		config.paths.base_model_dir, config.paths.model_name_prefix + model_name)
	config.paths.best_model_dir = path.join(config.paths.model_dir, 'best')

	for model_dir in [config.paths.model_dir, config.paths.best_model_dir]:
		if not path.exists(model_dir):
			os.makedirs(model_dir)

	if config.paths.model_path is None:
		config.paths.model_path = path.join(config.paths.model_dir, config.paths.model_filename)
		config.paths.best_model_path = path.join(
			config.paths.best_model_dir, config.paths.model_filename)

	if config.paths.best_model_path is None and (config.paths.model_path is not None):
		config.paths.best_model_path = config.paths.model_path

	# Wandb Initialization
	wandb.init(
		id=model_name, project="Coreference", config=dict(config), resume=True,
		notes="Thesis updates", tags="thesis",
	)
	Experiment(config)


if __name__ == "__main__":
	# import sys
	# sys.argv.append(f'hydra.run.dir={os.path.expanduser("~")}')
	main()
