.PHONY: random nearest dqn game

random:
	python -m src_code.auto_pilot.run_policy --policy_type random

nearest:
	python -m src_code.auto_pilot.run_policy --policy_type nearest

dqn:
	python -m src_code.auto_pilot.run_policy --policy_type dqn

game:
	python -m src_code.main